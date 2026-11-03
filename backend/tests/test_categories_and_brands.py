import pytest

from catalog.models import Product


@pytest.mark.django_db
class TestCategories:
    def test_lists_all_categories_with_full_path_and_leaf_flag(self, api_client, categories):
        response = api_client.get("/api/categories/")

        assert response.status_code == 200
        by_slug = {c["slug"]: c for c in response.json()}
        assert by_slug["cream-biscuits"]["full_path"] == "Food › Biscuits › Cream Biscuits"
        assert by_slug["cream-biscuits"]["is_leaf"] is True
        assert by_slug["food"]["is_leaf"] is False

    def test_categories_are_read_only(self, api_client, user):
        api_client.force_authenticate(user=user)

        response = api_client.post("/api/categories/", {"name": "X", "slug": "x"}, format="json")

        assert response.status_code == 405


@pytest.mark.django_db
class TestBrands:
    def test_lists_distinct_brands_sorted(self, api_client, user, categories):
        for name, brand in [("A", "Parle"), ("B", "Britannia"), ("C", "Parle")]:
            Product.objects.create(
                name=name,
                brand=brand,
                category=categories["food"],
                description="x",
                price=10,
                created_by=user,
            )

        response = api_client.get("/api/brands/")

        assert response.json() == ["Britannia", "Parle"]
