from datetime import timedelta

import pytest
from django.utils import timezone

from catalog.models import Category, Product

LIST = "/api/products/"


@pytest.fixture
def catalog(user, categories):
    """
    A small catalog for search / filter / sort tests:

      name              brand      category         price
      Parle-G           Parle      Biscuits          10
      Hide & Seek       Parle      Cream Biscuits    30
      Good Day Cashew   Britannia  Cream Biscuits    40
      Marie Gold        Britannia  Biscuits          25
      Frooti            Parle Agro Beverages         20
    """
    rows = [
        ("Parle-G", "Parle", "biscuits", "10.00", "Classic glucose biscuit."),
        ("Hide & Seek", "Parle", "cream", "30.00", "Chocolate chip cookies."),
        ("Good Day Cashew", "Britannia", "cream", "40.00", "Rich cashew cookies."),
        ("Marie Gold", "Britannia", "biscuits", "25.00", "Light tea-time biscuit."),
        ("Frooti", "Parle Agro", "beverages", "20.00", "Mango fruit drink."),
    ]
    products = {}
    now = timezone.now()
    for index, (name, brand, category_key, price, description) in enumerate(rows):
        product = Product.objects.create(
            name=name,
            brand=brand,
            category=categories[category_key],
            price=price,
            description=description,
            created_by=user,
        )
        # Give each product a distinct created_at (oldest first), so date sorting is testable.
        Product.objects.filter(pk=product.pk).update(created_at=now - timedelta(days=len(rows) - index))
        products[name] = product
    return products


def names(response):
    return [p["name"] for p in response.json()["results"]]


@pytest.mark.django_db
class TestSearch:
    def test_search_by_name_is_case_insensitive(self, api_client, catalog):
        assert names(api_client.get(LIST, {"search": "good day"})) == ["Good Day Cashew"]

    def test_search_by_brand(self, api_client, catalog):
        assert set(names(api_client.get(LIST, {"search": "britannia"}))) == {"Good Day Cashew", "Marie Gold"}

    def test_search_by_description(self, api_client, catalog):
        assert names(api_client.get(LIST, {"search": "glucose"})) == ["Parle-G"]

    def test_search_with_no_match_returns_empty_list(self, api_client, catalog):
        response = api_client.get(LIST, {"search": "maggi"})

        assert response.status_code == 200
        assert response.json()["count"] == 0


@pytest.mark.django_db
class TestFilters:
    def test_brand_filter_is_exact_but_ignores_case(self, api_client, catalog):
        # "parle" must NOT match "Parle Agro".
        assert set(names(api_client.get(LIST, {"brand": "parle"}))) == {"Parle-G", "Hide & Seek"}

    def test_category_filter_includes_sub_categories(self, api_client, catalog):
        result = set(names(api_client.get(LIST, {"category": "biscuits"})))

        assert result == {"Parle-G", "Marie Gold", "Hide & Seek", "Good Day Cashew"}

    def test_top_level_category_includes_all_levels(self, api_client, catalog):
        assert len(names(api_client.get(LIST, {"category": "food"}))) == 4

    def test_leaf_category_filter(self, api_client, catalog):
        assert set(names(api_client.get(LIST, {"category": "cream-biscuits"}))) == {
            "Hide & Seek",
            "Good Day Cashew",
        }

    def test_unknown_category_returns_no_results_not_error(self, api_client, catalog):
        response = api_client.get(LIST, {"category": "does-not-exist"})

        assert response.status_code == 200
        assert response.json()["count"] == 0

    def test_price_range_is_inclusive(self, api_client, catalog):
        result = set(names(api_client.get(LIST, {"min_price": "20", "max_price": "30"})))

        assert result == {"Frooti", "Marie Gold", "Hide & Seek"}

    def test_min_price_above_max_price_is_validation_error(self, api_client, catalog):
        response = api_client.get(LIST, {"min_price": "50", "max_price": "10"})

        assert response.status_code == 400
        assert "min_price" in response.json()["error"]["details"]

    def test_non_numeric_price_is_validation_error(self, api_client, catalog):
        response = api_client.get(LIST, {"max_price": "cheap"})

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "validation_error"

    def test_filters_and_search_combine(self, api_client, catalog):
        params = {"search": "cookies", "brand": "Britannia", "max_price": "45"}

        assert names(api_client.get(LIST, params)) == ["Good Day Cashew"]


@pytest.mark.django_db
class TestOrdering:
    def test_default_is_newest_first(self, api_client, catalog):
        assert names(api_client.get(LIST))[0] == "Frooti"

    def test_price_ascending(self, api_client, catalog):
        prices = [p["price"] for p in api_client.get(LIST, {"ordering": "price"}).json()["results"]]

        assert prices == ["10.00", "20.00", "25.00", "30.00", "40.00"]

    def test_price_descending(self, api_client, catalog):
        assert names(api_client.get(LIST, {"ordering": "-price"}))[0] == "Good Day Cashew"

    def test_name_ascending(self, api_client, catalog):
        assert names(api_client.get(LIST, {"ordering": "name"}))[0] == "Frooti"

    def test_created_at_ascending(self, api_client, catalog):
        assert names(api_client.get(LIST, {"ordering": "created_at"}))[0] == "Parle-G"

    def test_unknown_ordering_field_is_ignored(self, api_client, catalog):
        # e.g. ?ordering=gtin is not allowed: falls back to the default order.
        response = api_client.get(LIST, {"ordering": "gtin"})

        assert response.status_code == 200
        assert names(response)[0] == "Frooti"


@pytest.mark.django_db
class TestPagination:
    @pytest.fixture
    def many_products(self, user, categories):
        Product.objects.bulk_create(
            Product(
                name=f"Product {i:02d}",
                brand="Same Brand",
                category=categories["food"],
                description="x",
                price="10.00",  # all the same price: tests the id tie-breaker
                created_by=user,
            )
            for i in range(30)
        )

    def test_default_page_size_is_12(self, api_client, many_products):
        body = api_client.get(LIST).json()

        assert body["count"] == 30
        assert len(body["results"]) == 12
        assert body["next"] is not None
        assert body["previous"] is None

    def test_custom_page_size(self, api_client, many_products):
        assert len(api_client.get(LIST, {"page_size": 5}).json()["results"]) == 5

    def test_page_size_is_capped_at_100(self, api_client, user, categories):
        Product.objects.bulk_create(
            Product(name=f"P{i}", brand="B", category=categories["food"], description="x", price=1)
            for i in range(105)
        )

        assert len(api_client.get(LIST, {"page_size": 500}).json()["results"]) == 100

    def test_out_of_range_page_is_404_in_standard_format(self, api_client, many_products):
        response = api_client.get(LIST, {"page": 99})

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "not_found"

    def test_equal_prices_never_repeat_or_skip_across_pages(self, api_client, many_products):
        seen = []
        for page in (1, 2, 3):
            response = api_client.get(LIST, {"ordering": "price", "page": page})
            seen.extend(p["id"] for p in response.json()["results"])

        assert len(seen) == len(set(seen)) == 30


@pytest.mark.django_db
class TestCategoryDescendants:
    def test_descendant_ids_cover_every_level(self, categories):
        ids = set(categories["food"].descendant_ids())

        assert ids == {categories["food"].id, categories["biscuits"].id, categories["cream"].id}

    def test_leaf_has_only_itself(self, categories):
        assert Category.objects.get(slug="cream-biscuits").descendant_ids() == [categories["cream"].id]


@pytest.mark.django_db
class TestApiDocs:
    @pytest.mark.parametrize("url", ["/api/schema/", "/api/docs/", "/api/redoc/"])
    def test_docs_pages_load(self, api_client, url):
        assert api_client.get(url).status_code == 200

    def test_schema_lists_product_filters(self, api_client):
        schema = api_client.get("/api/schema/", {"format": "json"}).json()

        params = {p["name"] for p in schema["paths"]["/api/products/"]["get"]["parameters"]}
        assert {"search", "brand", "category", "min_price", "max_price", "ordering", "page"} <= params
