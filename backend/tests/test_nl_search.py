import pytest
from rest_framework.throttling import ScopedRateThrottle

from ai.serializers.parsed_search_serializer import ParsedSearchSerializer
from catalog.models import Product
from services.claude_client import ClaudeClient
from tests.ai_fakes import FakeSDK, claude_response

PARSE = "/api/ai/parse-search/"
CONTEXT = {"brands": ["Britannia", "Parle"], "category_slugs": {"biscuits", "cookies"}}


def whitelist(data):
    serializer = ParsedSearchSerializer(data=data, context=CONTEXT)
    assert serializer.is_valid(), serializer.errors
    return serializer.validated_data


class TestWhitelist:
    def test_good_answer_passes_through(self):
        result = whitelist(
            {
                "search": "cashew",
                "brand": "Britannia",
                "category": "cookies",
                "max_price": 50,
                "ordering": "price",
            }
        )

        assert result["brand"] == "Britannia" and result["category"] == "cookies"
        assert str(result["max_price"]) == "50.00" and result["ordering"] == "price"

    def test_unknown_brand_is_dropped(self):
        assert whitelist({"brand": "Oreo Corp"})["brand"] == ""

    def test_brand_case_is_fixed_to_catalog_spelling(self):
        assert whitelist({"brand": "britannia"})["brand"] == "Britannia"

    def test_unknown_category_is_dropped(self):
        assert whitelist({"category": "electronics"})["category"] == ""

    @pytest.mark.parametrize("ordering", ["gtin", "-readiness_score", "price; DROP TABLE", "random"])
    def test_bad_ordering_is_dropped(self, ordering):
        assert whitelist({"ordering": ordering})["ordering"] == ""

    def test_extra_keys_are_ignored(self):
        result = whitelist({"brand": "Parle", "created_by": 1, "sql": "DELETE FROM catalog_product"})

        assert set(result) == {"search", "brand", "category", "min_price", "max_price", "ordering"}

    @pytest.mark.parametrize("value", [-5, "cheap", True, [10], {"a": 1}])
    def test_bad_prices_are_dropped(self, value):
        result = whitelist({"min_price": value, "max_price": value})

        assert result["min_price"] is None and result["max_price"] is None

    def test_reversed_price_range_is_swapped(self):
        result = whitelist({"min_price": 50, "max_price": 20})

        assert (str(result["min_price"]), str(result["max_price"])) == ("20.00", "50.00")

    def test_null_prices_mean_no_limit(self):
        result = whitelist({"min_price": None, "max_price": None})

        assert result["min_price"] is None and result["max_price"] is None

    def test_missing_keys_get_safe_defaults(self):
        assert whitelist({}) == {
            "search": "",
            "brand": "",
            "category": "",
            "min_price": None,
            "max_price": None,
            "ordering": "",
        }


@pytest.fixture
def catalog_for_search(user, categories):
    for name, brand, category, price in [
        ("Good Day Cashew", "Britannia", "cream", "40.00"),
        ("Parle-G", "Parle", "biscuits", "10.00"),
    ]:
        Product.objects.create(
            name=name,
            brand=brand,
            category=categories[category],
            description="x",
            price=price,
            created_by=user,
        )


@pytest.fixture
def fake_claude(monkeypatch, settings):
    settings.ANTHROPIC_API_KEY = "test-key"

    def install(*answers):
        sdk = FakeSDK(*answers)
        monkeypatch.setattr(ClaudeClient, "_client", lambda self: sdk)
        return sdk

    return install


@pytest.mark.django_db
class TestParseSearchEndpoint:
    def test_turns_a_sentence_into_whitelisted_filters(self, api_client, catalog_for_search, fake_claude):
        sdk = fake_claude(
            claude_response(
                {
                    "search": "",
                    "brand": "britannia",
                    "category": "biscuits",
                    "min_price": None,
                    "max_price": 50,
                    "ordering": "price",
                    "delete_everything": True,
                }
            )
        )

        response = api_client.post(
            PARSE, {"query": "Britannia biscuits under ₹50, cheapest first"}, format="json"
        )

        assert response.status_code == 200
        assert response.json() == {
            "filters": {
                "search": "",
                "brand": "Britannia",
                "category": "biscuits",
                "min_price": None,
                "max_price": 50.0,
                "ordering": "price",
            },
            "cached": False,
        }
        sent = sdk.calls[0]
        assert sent["model"] == "claude-haiku-5-5"
        schema = sent["output_config"]["format"]["schema"]["properties"]
        assert "Britannia" in schema["brand"]["enum"] and "biscuits" in schema["category"]["enum"]

    def test_filters_work_with_the_normal_product_list(self, api_client, catalog_for_search, fake_claude):
        answer = {"search": "", "brand": "Britannia", "category": "biscuits", "min_price": None,
                  "max_price": 50, "ordering": "price"}  # fmt: skip
        fake_claude(claude_response(answer))
        filters = api_client.post(PARSE, {"query": "britannia biscuits under 50"}, format="json").json()[
            "filters"
        ]

        params = {key: value for key, value in filters.items() if value not in ("", None)}
        names = [p["name"] for p in api_client.get("/api/products/", params).json()["results"]]

        assert names == ["Good Day Cashew"]

    @pytest.mark.parametrize(
        ("answer", "expected"),
        [
            ({"search": "packets left", "brand": "Parle"}, ""),  # "how many Maggie packets left"
            ({"search": "products", "ordering": "price"}, ""),  # "give me cheapest products"
            ({"search": "packets glucose", "brand": "Parle"}, ""),  # no Parle product says "glucose"
            ({"search": "cashew packets", "brand": "Britannia"}, "cashew"),  # useful words stay
            ({"search": "unicorn"}, "unicorn"),  # nothing else understood: an honest empty result
        ],
    )
    def test_search_words_that_find_nothing_are_dropped(
        self, api_client, catalog_for_search, fake_claude, answer, expected
    ):
        empty = {
            "search": "",
            "brand": "",
            "category": "",
            "min_price": None,
            "max_price": None,
            "ordering": "",
        }
        fake_claude(claude_response({**empty, **answer}))

        filters = api_client.post(PARSE, {"query": "a shopper's sentence"}, format="json").json()["filters"]

        assert filters["search"] == expected

    def test_identical_query_is_cached(self, api_client, catalog_for_search, fake_claude):
        answer = {"search": "", "brand": "Parle", "category": "", "min_price": None, "max_price": None,
                  "ordering": ""}  # fmt: skip
        sdk = fake_claude(claude_response(answer))

        first = api_client.post(PARSE, {"query": "Parle biscuits"}, format="json").json()
        second = api_client.post(PARSE, {"query": "  parle   BISCUITS "}, format="json").json()

        assert first["cached"] is False and second["cached"] is True
        assert second["filters"] == first["filters"]
        assert len(sdk.calls) == 1  # Claude was asked only once

    def test_no_login_needed(self, api_client, catalog_for_search, fake_claude):
        fake_claude(claude_response({"search": "masala", "brand": "", "category": "", "min_price": None,
                                     "max_price": None, "ordering": ""}))  # fmt: skip

        assert api_client.post(PARSE, {"query": "masala"}, format="json").status_code == 200

    def test_query_is_required(self, api_client, db):
        response = api_client.post(PARSE, {"query": " "}, format="json")

        assert response.status_code == 400
        assert "query" in response.json()["error"]["details"]

    def test_ai_off_returns_503_so_the_frontend_falls_back(self, api_client, db, settings):
        settings.ANTHROPIC_API_KEY = ""

        response = api_client.post(PARSE, {"query": "cheap biscuits"}, format="json")

        assert response.status_code == 503
        assert response.json()["error"]["code"] == "ai_not_configured"

    def test_ai_search_has_its_own_rate_limit(self, api_client, catalog_for_search, fake_claude, monkeypatch):
        monkeypatch.setitem(ScopedRateThrottle.THROTTLE_RATES, "ai_search", "2/hour")
        answer = {
            "search": "",
            "brand": "",
            "category": "",
            "min_price": None,
            "max_price": None,
            "ordering": "",
        }
        fake_claude(claude_response(answer), claude_response(answer))

        statuses = [
            api_client.post(PARSE, {"query": f"query {i}"}, format="json").status_code for i in range(3)
        ]

        assert statuses == [200, 200, 429]
