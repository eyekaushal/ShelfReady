from django.core.management.base import BaseCommand

from catalog.models import Product
from services.embedding_service import EmbeddingService
from services.lookalike_service import LookalikeService


class Command(BaseCommand):
    """python manage.py analyze_catalog: measure what's missing, then recheck every look-alike pair."""

    help = "Measure images and compute embeddings that are missing, then refresh look-alike pairs."

    def handle(self, *args, **options):
        products = list(Product.objects.select_related("category").order_by("id"))
        for product in products:
            # Seed rows skip the API, so nothing has analysed them yet. Measured rows are skipped.
            needs_image = bool(product.image_url) and not product.image_phash
            needs_text = EmbeddingService.is_enabled() and product.name_embedding is None
            if needs_image or needs_text:
                LookalikeService.analyze(product, image_changed=needs_image, text_changed=needs_text)

        # A second pass: while the first ran, earlier products couldn't see later ones' fingerprints.
        for product in products:
            LookalikeService.refresh_pairs(product)

        self.stdout.write(self.style.SUCCESS(f"Analysed {len(products)} products."))
