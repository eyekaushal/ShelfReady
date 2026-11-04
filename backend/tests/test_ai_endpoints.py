import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.throttling import ScopedRateThrottle

from services.claude_client import ClaudeClient
from tests.ai_fakes import FakeSDK, claude_response, png_bytes

EXTRACT = "/api/ai/extract-product/"
DESCRIBE = "/api/ai/generate-description/"

CLAUDE_EXTRACT_ANSWER = {
    "name": "Good Day Cashew Cookies",
    "brand": "Britannia",
    "category_slug": "cream-biscuits",
    "variant": "Cashew",
    "pack_size": "200 g",
    "description": "Cashew cookies from Britannia's Good Day range in a 200 g pack.",
    "tags": ["Cookies", "cashew", "cookies", "tea time"],
    "confidence": {
        "name": "high",
        "brand": "high",
        "category": "medium",
        "variant": "high",
        "pack_size": "medium",
        "description": "medium",
        "tags": "medium",
    },
    "notes": "",
}


@pytest.fixture
def fake_claude(monkeypatch, settings):
    """Turn AI on and make every ClaudeClient use a FakeSDK with the answers we queue."""
    settings.ANTHROPIC_API_KEY = "test-key"

    def install(*answers):
        sdk = FakeSDK(*answers)
        monkeypatch.setattr(ClaudeClient, "_client", lambda self: sdk)
        return sdk

    return install


def upload(content=None):
    return SimpleUploadedFile("pack.png", content or png_bytes(), content_type="image/png")


@pytest.mark.django_db
class TestStatus:
    def test_disabled_without_key(self, api_client, settings):
        settings.ANTHROPIC_API_KEY = ""

        assert api_client.get("/api/ai/status/").json() == {"enabled": False}

    def test_enabled_with_key(self, api_client, settings):
        settings.ANTHROPIC_API_KEY = "test-key"

        assert api_client.get("/api/ai/status/").json() == {"enabled": True}


@pytest.mark.django_db
class TestExtractProduct:
    def test_needs_login(self, api_client):
        assert api_client.post(EXTRACT, {"image": upload()}, format="multipart").status_code == 401

    def test_upload_returns_prefill_fields(self, auth_client, categories, fake_claude):
        sdk = fake_claude(claude_response(CLAUDE_EXTRACT_ANSWER))

        response = auth_client.post(EXTRACT, {"image": upload()}, format="multipart")

        assert response.status_code == 200
        body = response.json()
        assert body["fields"]["name"] == "Good Day Cashew Cookies"
        assert body["fields"]["category"] == categories["cream"].id  # slug → id for the form
        assert body["fields"]["tags"] == ["cookies", "cashew", "tea time"]
        assert body["confidence"]["pack_size"] == "medium"
        # The photo and the category whitelist both went to Claude.
        sent = sdk.calls[0]
        assert sent["messages"][0]["content"][0]["source"]["media_type"] == "image/png"
        assert (
            "cream-biscuits"
            in sent["output_config"]["format"]["schema"]["properties"]["category_slug"]["enum"]
        )

    def test_nothing_is_saved(self, auth_client, categories, fake_claude):
        from catalog.models import Product

        fake_claude(claude_response(CLAUDE_EXTRACT_ANSWER))
        auth_client.post(EXTRACT, {"image": upload()}, format="multipart")

        assert Product.objects.count() == 0

    def test_unknown_category_becomes_empty(self, auth_client, categories, fake_claude):
        fake_claude(claude_response({**CLAUDE_EXTRACT_ANSWER, "category_slug": "none"}))

        body = auth_client.post(EXTRACT, {"image": upload()}, format="multipart").json()

        assert body["fields"]["category"] is None

    def test_extra_keys_from_the_model_are_dropped(self, auth_client, categories, fake_claude):
        # e.g. text on the pack tried to make the model add fields or actions.
        answer = {**CLAUDE_EXTRACT_ANSWER, "price": "1", "delete_all_products": True}
        fake_claude(claude_response(answer))

        body = auth_client.post(EXTRACT, {"image": upload()}, format="multipart").json()

        assert "price" not in body["fields"] and "delete_all_products" not in body

    def test_image_url_goes_through_the_safe_fetch(self, auth_client, categories, fake_claude):
        fake_claude()  # Claude must never be called for a blocked URL

        response = auth_client.post(EXTRACT, {"image_url": "http://169.254.169.254/latest"}, format="json")

        assert response.status_code == 400
        assert "private network" in response.json()["error"]["details"]["image_url"][0]

    @pytest.mark.parametrize("payload", [{}, {"image_url": "https://x.com/a.png", "image": "file"}])
    def test_exactly_one_input(self, auth_client, payload, fake_claude):
        fake_claude()
        if "image" in payload:
            payload = {**payload, "image": upload()}

        response = auth_client.post(EXTRACT, payload, format="multipart")

        assert response.status_code == 400
        assert "non_field_errors" in response.json()["error"]["details"]

    def test_not_an_image(self, auth_client, fake_claude):
        fake_claude()

        response = auth_client.post(EXTRACT, {"image": upload(b"hello")}, format="multipart")

        assert response.status_code == 400
        assert "image" in response.json()["error"]["details"]

    def test_ai_not_configured_is_a_clean_503(self, auth_client, categories, settings):
        settings.ANTHROPIC_API_KEY = ""

        response = auth_client.post(EXTRACT, {"image": upload()}, format="multipart")

        assert response.status_code == 503
        assert response.json()["error"]["code"] == "ai_not_configured"

    def test_no_image_is_fetched_when_ai_is_off(self, auth_client, settings, monkeypatch):
        settings.ANTHROPIC_API_KEY = ""
        fetched = []
        monkeypatch.setattr(
            "services.image_service.ImageService.fetch_url", lambda *a, **k: fetched.append(a)
        )

        auth_client.post(EXTRACT, {"image_url": "https://cdn.example.com/a.png"}, format="json")

        assert fetched == []

    def test_bad_ai_output_twice_is_a_clean_502(self, auth_client, categories, fake_claude):
        fake_claude(claude_response(text="garbage"), claude_response({"name": "only a name"}))

        response = auth_client.post(EXTRACT, {"image": upload()}, format="multipart")

        assert response.status_code == 502
        assert response.json()["error"]["code"] == "ai_invalid_output"


@pytest.mark.django_db
class TestGenerateDescription:
    def test_returns_description_and_tags(self, auth_client, categories, fake_claude):
        sdk = fake_claude(
            claude_response(
                {"description": "Glucose biscuits from Parle in a 250 g pack.", "tags": ["Biscuits"]}
            )
        )

        response = auth_client.post(
            DESCRIBE,
            {
                "name": "Parle-G",
                "brand": "Parle",
                "category": categories["biscuits"].id,
                "pack_size": "250 g",
            },
            format="json",
        )

        assert response.status_code == 200
        assert response.json() == {
            "description": "Glucose biscuits from Parle in a 250 g pack.",
            "tags": ["biscuits"],
        }
        prompt = sdk.calls[0]["messages"][0]["content"][0]["text"]
        assert "Food › Biscuits" in prompt and "250 g" in prompt
        assert sdk.calls[0]["model"] == "claude-haiku-5-5"  # the fast model

    def test_needs_name_and_brand(self, auth_client):
        response = auth_client.post(DESCRIBE, {"name": "X"}, format="json")

        assert response.status_code == 400
        assert {"name", "brand"} <= set(response.json()["error"]["details"])

    def test_needs_login(self, api_client):
        assert (
            api_client.post(DESCRIBE, {"name": "Parle-G", "brand": "Parle"}, format="json").status_code == 401
        )


@pytest.mark.django_db
class TestThrottle:
    def test_ai_calls_are_rate_limited_per_user(self, auth_client, monkeypatch, fake_claude):
        monkeypatch.setitem(ScopedRateThrottle.THROTTLE_RATES, "ai", "2/hour")
        good = {"description": "Glucose biscuits from Parle in a 250 g pack.", "tags": []}
        fake_claude(claude_response(good), claude_response(good))

        statuses = [
            auth_client.post(DESCRIBE, {"name": "Parle-G", "brand": "Parle"}, format="json").status_code
            for _ in range(3)
        ]

        assert statuses == [200, 200, 429]
