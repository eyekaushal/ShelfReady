import json
import logging
import time

import anthropic
from django.conf import settings
from rest_framework import status

from services.ai_service_error import AIServiceError

logger = logging.getLogger("shelfready.ai")


class ClaudeClient:
    """
    The only place the backend talks to Claude.

    One method, `generate_json`: send a prompt (text and/or an image), get back validated data.
    On top of the SDK it adds:
    - a clean "AI unavailable" error when no API key is configured,
    - one log line per call (task, model, latency, tokens, outcome; never the key or the image),
    - Anthropic errors translated into AIServiceError codes the frontend understands.

    Structured outputs (`output_config.format`) make Claude answer with JSON that follows our
    schema. We still validate that JSON with a DRF serializer, because the model's output is
    untrusted data. If the JSON is broken or fails validation, we ask once more, then give up
    with a clean "ai_invalid_output" error.
    """

    # Models that support the server-side refusal fallback. If Claude's safety check declines a
    # request, the API retries it on a suitable fallback model inside the same call.
    FALLBACK_MODELS = {"claude-sonnet-5-5", "claude-opus-5-5", "claude-opus-5", "claude-fable-5-1"}
    FALLBACK_BETA = "server-side-fallback-2026-07-01"

    def __init__(self, sdk_client=None):
        # Tests pass a fake SDK client; real code builds one lazily on first use.
        self._sdk_client = sdk_client

    @staticmethod
    def is_configured() -> bool:
        return bool(settings.ANTHROPIC_API_KEY)

    def generate_json(
        self,
        *,
        task: str,
        model: str,
        system: str,
        content: list[dict],
        schema: dict,
        serializer_class,
        serializer_context: dict | None = None,
        max_tokens: int = 4000,
        effort: str = "low",
    ) -> dict:
        """
        task:             short name for logs, e.g. "extract_product"
        content:          user message blocks, e.g. [{"type": "image", ...}, {"type": "text", ...}]
        schema:           JSON schema the answer must follow
        serializer_class: DRF serializer that validates the answer; its validated_data is returned
        effort:           "low" for simple jobs (cheaper, faster); "medium" when reading needs care
        """
        if not self.is_configured() and self._sdk_client is None:
            raise AIServiceError("ai_not_configured", "AI features are not set up on this server.")

        for attempt in (1, 2):
            try:
                data = self._call(task, model, system, content, schema, max_tokens, effort)
            except AIServiceError as error:
                if error.detail.code == "ai_invalid_output" and attempt == 1:
                    continue  # broken JSON: ask once more
                raise
            serializer = serializer_class(data=data, context=serializer_context or {})
            if serializer.is_valid():
                return serializer.validated_data
            logger.warning(
                "ai output failed validation",
                extra={"ai_task": task, "attempt": attempt, "fields": sorted(serializer.errors)},
            )

        raise AIServiceError(
            "ai_invalid_output",
            "The AI's answer didn't pass our checks. Please try again or fill the form manually.",
            status.HTTP_502_BAD_GATEWAY,
        )

    # --- helpers -------------------------------------------------------------------

    def _call(self, task, model, system, content, schema, max_tokens, effort) -> dict:
        """One request to Claude → the parsed JSON dict (not yet validated)."""
        request = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": content}],
            "output_config": {"effort": effort, "format": {"type": "json_schema", "schema": schema}},
        }
        if model in self.FALLBACK_MODELS:
            request["betas"] = [self.FALLBACK_BETA]
            request["fallbacks"] = "default"

        started = time.perf_counter()
        try:
            response = self._client().beta.messages.create(**request)
        except anthropic.APIError as error:
            self._log(task, model, started, outcome=type(error).__name__)
            raise self._translate(error) from error

        usage = getattr(response, "usage", None)
        self._log(
            task,
            model,
            started,
            outcome=response.stop_reason,
            input_tokens=getattr(usage, "input_tokens", None),
            output_tokens=getattr(usage, "output_tokens", None),
            anthropic_request_id=getattr(response, "_request_id", None),
        )

        if response.stop_reason == "refusal":
            raise AIServiceError(
                "ai_refused",
                "The AI couldn't process this input. Please fill the form manually.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return self._parse_json(response)

    def _client(self):
        if self._sdk_client is None:
            # max_retries=1: the SDK already retries 429 / 5xx / network errors once with backoff.
            self._sdk_client = anthropic.Anthropic(
                api_key=settings.ANTHROPIC_API_KEY,
                timeout=settings.AI_TIMEOUT_SECONDS,
                max_retries=1,
            )
        return self._sdk_client

    @staticmethod
    def _parse_json(response) -> dict:
        # With output_config.format the answer is one text block holding the JSON.
        # If it got cut off (stop_reason "max_tokens") or isn't valid JSON, the caller retries.
        text = next((block.text for block in response.content if block.type == "text"), "")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as error:
            raise AIServiceError(
                "ai_invalid_output", "The AI returned an unreadable answer.", status.HTTP_502_BAD_GATEWAY
            ) from error
        if not isinstance(data, dict):
            raise AIServiceError(
                "ai_invalid_output", "The AI returned an unexpected answer.", status.HTTP_502_BAD_GATEWAY
            )
        return data

    @staticmethod
    def _translate(error: anthropic.APIError) -> AIServiceError:
        # Most specific first: these are all subclasses of APIStatusError / APIConnectionError.
        if isinstance(error, (anthropic.AuthenticationError, anthropic.PermissionDeniedError)):
            # Wrong or revoked key: an operator problem, so users just see "AI unavailable".
            return AIServiceError("ai_not_configured", "AI features are not available right now.")
        if isinstance(
            error, (anthropic.RateLimitError, anthropic.OverloadedError, anthropic.APIConnectionError)
        ):
            # Rate limit, overload, network trouble or timeout (APITimeoutError is a connection error).
            return AIServiceError("ai_busy", "The AI service is busy. Please try again in a minute.")
        if isinstance(error, anthropic.APIStatusError) and error.status_code >= 500:
            return AIServiceError("ai_busy", "The AI service is having trouble. Please try again soon.")
        return AIServiceError(
            "ai_error",
            "The AI request failed. Please try again or fill the form manually.",
            status.HTTP_502_BAD_GATEWAY,
        )

    @staticmethod
    def _log(task, model, started, outcome, **fields):
        logger.info(
            "ai call",
            extra={
                "ai_task": task,
                "ai_model": model,
                "latency_ms": round((time.perf_counter() - started) * 1000),
                "outcome": outcome,  # e.g. "end_turn", "refusal", "RateLimitError"
                **{key: value for key, value in fields.items() if value is not None},
            },
        )
