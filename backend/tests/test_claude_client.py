import logging

import anthropic
import httpx2
import pytest

from ai.serializers.generated_description_serializer import GeneratedDescriptionSerializer
from services.ai_service_error import AIServiceError
from services.claude_client import ClaudeClient
from tests.ai_fakes import FakeSDK, claude_response

GOOD = {
    "description": "Crunchy cashew cookies from Britannia, sold in a 200 g pack.",
    "tags": ["Cookies", "cashew"],
}


def call(client, model="claude-haiku-5-5"):
    return client.generate_json(
        task="test",
        model=model,
        system="system prompt",
        content=[{"type": "text", "text": "hi"}],
        schema={"type": "object"},
        serializer_class=GeneratedDescriptionSerializer,
    )


def api_error(cls, status_code):
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    return cls("boom", response=httpx2.Response(status_code, request=request), body=None)


def code_of(excinfo):
    return excinfo.value.detail.code


class TestHappyPath:
    def test_returns_validated_data(self):
        sdk = FakeSDK(claude_response(GOOD))

        result = call(ClaudeClient(sdk))

        assert result["tags"] == ["cookies", "cashew"]  # cleaned by the serializer
        assert len(sdk.calls) == 1

    def test_sends_json_schema_and_effort(self):
        sdk = FakeSDK(claude_response(GOOD))

        call(ClaudeClient(sdk))

        sent = sdk.calls[0]
        assert sent["output_config"]["format"]["type"] == "json_schema"
        assert sent["output_config"]["effort"] == "low"
        assert "temperature" not in sent  # rejected by current models

    def test_fallback_only_for_models_that_support_it(self):
        sdk = FakeSDK(claude_response(GOOD), claude_response(GOOD))

        call(ClaudeClient(sdk), model="claude-sonnet-5-5")
        call(ClaudeClient(sdk), model="claude-haiku-5-5")

        assert sdk.calls[0]["fallbacks"] == "default"
        assert sdk.calls[0]["betas"] == [ClaudeClient.FALLBACK_BETA]
        assert "fallbacks" not in sdk.calls[1]


class TestRetryAndValidation:
    def test_broken_json_is_retried_once(self):
        sdk = FakeSDK(claude_response(text="{not json"), claude_response(GOOD))

        assert call(ClaudeClient(sdk))["description"].startswith("Crunchy")
        assert len(sdk.calls) == 2

    def test_invalid_answer_is_retried_once(self):
        sdk = FakeSDK(claude_response({"description": "short", "tags": []}), claude_response(GOOD))

        call(ClaudeClient(sdk))

        assert len(sdk.calls) == 2

    def test_gives_up_after_two_bad_answers(self):
        sdk = FakeSDK(claude_response({"tags": []}), claude_response(text="nope"))

        with pytest.raises(AIServiceError) as excinfo:
            call(ClaudeClient(sdk))

        assert code_of(excinfo) == "ai_invalid_output"
        assert excinfo.value.status_code == 502

    def test_refusal_is_not_retried(self):
        sdk = FakeSDK(claude_response(text="", stop_reason="refusal"))

        with pytest.raises(AIServiceError) as excinfo:
            call(ClaudeClient(sdk))

        assert code_of(excinfo) == "ai_refused"
        assert len(sdk.calls) == 1


class TestErrors:
    def test_no_api_key_means_not_configured(self, settings):
        settings.ANTHROPIC_API_KEY = ""

        with pytest.raises(AIServiceError) as excinfo:
            call(ClaudeClient())

        assert code_of(excinfo) == "ai_not_configured"
        assert excinfo.value.status_code == 503

    @pytest.mark.parametrize(
        ("error", "expected"),
        [
            (api_error(anthropic.AuthenticationError, 401), "ai_not_configured"),
            (api_error(anthropic.RateLimitError, 429), "ai_busy"),
            (api_error(anthropic.OverloadedError, 529), "ai_busy"),
            (api_error(anthropic.InternalServerError, 500), "ai_busy"),
            (api_error(anthropic.BadRequestError, 400), "ai_error"),
            (anthropic.APIConnectionError(request=httpx2.Request("POST", "https://x")), "ai_busy"),
        ],
    )
    def test_sdk_errors_become_clean_codes(self, error, expected):
        with pytest.raises(AIServiceError) as excinfo:
            call(ClaudeClient(FakeSDK(error)))

        assert code_of(excinfo) == expected


class TestLogging:
    def test_logs_model_latency_and_tokens_but_no_secrets(self, caplog, settings):
        settings.ANTHROPIC_API_KEY = "sk-ant-secret-value"
        caplog.set_level(logging.INFO, logger="shelfready.ai")

        call(ClaudeClient(FakeSDK(claude_response(GOOD))))

        record = next(r for r in caplog.records if r.getMessage() == "ai call")
        assert record.ai_model == "claude-haiku-5-5"
        assert record.input_tokens == 1200 and record.output_tokens == 150
        assert record.outcome == "end_turn"
        assert isinstance(record.latency_ms, int)
        assert "sk-ant-secret-value" not in caplog.text

    def test_failed_calls_are_logged_too(self, caplog):
        caplog.set_level(logging.INFO, logger="shelfready.ai")

        with pytest.raises(AIServiceError):
            call(ClaudeClient(FakeSDK(api_error(anthropic.RateLimitError, 429))))

        record = next(r for r in caplog.records if r.getMessage() == "ai call")
        assert record.outcome == "RateLimitError"


class TestShortDescriptions:
    def test_wordy_description_is_rejected_and_retried(self):
        wordy = {
            "description": "A yellow pouch with a bowl of noodles on the front. " * 8,
            "tags": ["noodles"],
        }
        short = {
            "description": "Masala-flavoured instant noodles from Maggi in a 70 g pack.",
            "tags": ["noodles"],
        }
        sdk = FakeSDK(claude_response(wordy), claude_response(short))

        result = call(ClaudeClient(sdk))

        assert result["description"] == short["description"]
        assert len(sdk.calls) == 2
