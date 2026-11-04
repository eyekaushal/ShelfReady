import json
from pathlib import Path

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command

from catalog.models import Category, Product
from services.catalog_seeder import CatalogSeeder
from services.gtin_validator import GtinValidator

SEED_FILE = Path(__file__).resolve().parent.parent / "seed" / "products.json"

SMALL_DATA = {
    "categories": [
        {"slug": "food", "name": "Food", "parent": None},
        {"slug": "biscuits", "name": "Biscuits", "parent": "food"},
    ],
    "products": [
        {
            "gtin": "8901719123870",
            "name": "Parle-G",
            "brand": "Parle",
            "category": "biscuits",
            "pack_size": "250 g",
            "variant": "",
            "price": "30.00",
            "image_url": "https://images.openfoodfacts.org/x.400.jpg",
            "description": "Parle-G by Parle, 250 g pack.",
            "tags": ["biscuits", "food"],
        }
    ],
}


@pytest.mark.django_db
class TestCatalogSeeder:
    def test_creates_categories_with_parents(self):
        CatalogSeeder(SMALL_DATA, demo_password="pw-12345678").run()

        assert Category.objects.get(slug="biscuits").full_path == "Food › Biscuits"

    def test_products_are_owned_by_demo_user_who_can_log_in(self, api_client):
        CatalogSeeder(SMALL_DATA, demo_password="pw-12345678").run()

        assert Product.objects.get().created_by.username == "demo"
        response = api_client.post(
            "/api/auth/login/", {"username": "demo", "password": "pw-12345678"}, format="json"
        )
        assert response.status_code == 200

    def test_running_twice_does_not_duplicate(self):
        first = CatalogSeeder(SMALL_DATA, demo_password="pw").run()
        second = CatalogSeeder(SMALL_DATA, demo_password="pw").run()

        assert first["created"] == 1 and second == {"categories": 2, "created": 0, "updated": 1}
        assert Product.objects.count() == 1
        assert Category.objects.count() == 2
        assert User.objects.filter(username="demo").count() == 1

    def test_rerun_updates_changed_fields(self):
        CatalogSeeder(SMALL_DATA, demo_password="pw").run()
        changed = json.loads(json.dumps(SMALL_DATA))
        changed["products"][0]["price"] = "35.00"

        CatalogSeeder(changed, demo_password="pw").run()

        assert str(Product.objects.get().price) == "35.00"


@pytest.mark.django_db
class TestSeedCommandWithRealFile:
    def test_command_loads_the_committed_seed_file(self):
        call_command("seed_catalog")

        assert Product.objects.count() == len(json.loads(SEED_FILE.read_text())["products"])
        assert Product.objects.filter(created_by__username="demo").count() == Product.objects.count()


class TestSeedFileContents:
    """Guards the committed products.json, so a bad re-fetch can't slip in."""

    @pytest.fixture(scope="class")
    @classmethod
    def data(cls):
        return json.loads(SEED_FILE.read_text())

    def test_has_100_to_150_products(self, data):
        assert 100 <= len(data["products"]) <= 150

    def test_every_product_points_to_a_known_category(self, data):
        slugs = {c["slug"] for c in data["categories"]}
        assert all(p["category"] in slugs for p in data["products"])

    def test_parents_come_before_children(self, data):
        seen = set()
        for category in data["categories"]:
            assert category["parent"] is None or category["parent"] in seen
            seen.add(category["slug"])

    def test_prices_positive_and_gtins_unique(self, data):
        assert all(float(p["price"]) > 0 for p in data["products"])
        gtins = [p["gtin"] for p in data["products"]]
        assert len(gtins) == len(set(gtins))

    def test_images_are_on_the_fast_cdn_with_their_source_kept(self, data):
        # Open Food Facts can take many seconds per image: see seed/mirror_images_to_cloudinary.py.
        for product in data["products"]:
            assert product["image_url"].startswith("https://res.cloudinary.com/")
            assert "openfoodfacts" in product["source_image_url"]

    def test_demo_problems_are_present(self, data):
        notes = {p.get("demo_note") for p in data["products"]}
        assert {
            "invalid GTIN check digit",
            "image too small",
            "missing pack size (look-alike twin)",
            "duplicate of another product",
        } <= notes

    def test_only_the_demo_product_has_an_invalid_gtin(self, data):
        invalid = [p for p in data["products"] if not GtinValidator.is_valid(p["gtin"])]
        assert [p["demo_note"] for p in invalid] == ["invalid GTIN check digit"]

    def test_has_same_brand_twins(self, data):
        # At least one brand + base name appears in several pack sizes (look-alike material).
        parle_g = [p for p in data["products"] if p["name"].lower().startswith("parle-g")]
        assert len(parle_g) >= 2
