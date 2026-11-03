import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from services.catalog_seeder import CatalogSeeder

DEFAULT_FILE = Path(settings.BASE_DIR) / "seed" / "products.json"


class Command(BaseCommand):
    """python manage.py seed_catalog  → loads demo categories, demo user and products."""

    help = "Load the demo catalog (categories, demo user, products) from seed/products.json. Safe to re-run."

    def add_arguments(self, parser):
        parser.add_argument("--file", type=Path, default=DEFAULT_FILE)

    def handle(self, *args, **options):
        data = json.loads(options["file"].read_text())
        result = CatalogSeeder(data, demo_password=settings.SEED_DEMO_PASSWORD).run()
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {result['categories']} categories, "
                f"{result['created']} new + {result['updated']} updated products. "
                f"Demo login: {CatalogSeeder.DEMO_USERNAME}"
            )
        )
