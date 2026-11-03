from django.contrib.auth.models import User
from django.db import transaction

from catalog.models import Category, Product


class CatalogSeeder:
    """
    Loads seed/products.json into the database.

    Idempotent: running it twice gives the same result, because every row is matched
    on a stable key (category slug, demo username, product GTIN) and updated, not re-added.

    Writes go straight through the ORM, NOT the API serializer, on purpose: the seed
    includes a few deliberately bad rows (e.g. an invalid GTIN) that the API would reject,
    so the readiness score has real problems to find.
    """

    DEMO_USERNAME = "demo"
    DEMO_EMAIL = "demo@shelfready.app"

    def __init__(self, data: dict, demo_password: str):
        self.data = data
        self.demo_password = demo_password

    @transaction.atomic  # all or nothing: a crash halfway leaves the DB unchanged
    def run(self) -> dict:
        categories = self._seed_categories()
        demo_user = self._seed_demo_user()
        created, updated = self._seed_products(categories, demo_user)
        return {"categories": len(categories), "created": created, "updated": updated}

    def _seed_categories(self) -> dict[str, Category]:
        by_slug = {}
        # The JSON lists parents before children, so a parent always exists already.
        for row in self.data["categories"]:
            category, _ = Category.objects.update_or_create(
                slug=row["slug"],
                defaults={"name": row["name"], "parent": by_slug.get(row["parent"])},
            )
            by_slug[row["slug"]] = category
        return by_slug

    def _seed_demo_user(self) -> User:
        user, _ = User.objects.get_or_create(
            username=self.DEMO_USERNAME, defaults={"email": self.DEMO_EMAIL}
        )
        # Reset every run, so the password in the README always works.
        user.set_password(self.demo_password)
        user.save()
        return user

    def _seed_products(self, categories: dict[str, Category], owner: User) -> tuple[int, int]:
        created = updated = 0
        for row in self.data["products"]:
            _, was_created = Product.objects.update_or_create(
                gtin=row["gtin"],
                defaults={
                    "name": row["name"],
                    "brand": row["brand"],
                    "category": categories[row["category"]],
                    "description": row["description"],
                    "price": row["price"],
                    "image_url": row["image_url"],
                    "pack_size": row["pack_size"],
                    "variant": row["variant"],
                    "tags": row["tags"],
                    "created_by": owner,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1
        return created, updated
