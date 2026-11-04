import logging

from django.conf import settings
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from catalog.models import LookalikePair, Product
from services.embedding_service import EmbeddingService
from services.image_service import ImageService

logger = logging.getLogger("shelfready.lookalikes")


class LookalikeService:
    """
    Finds products a shelf camera could confuse.

    Candidates share a brand and a top-level category. A pair is flagged when their photos look
    alike (pHash) or their names read alike (text similarity). Then we compare pack size and
    variant: if those tell them apart, the catalog is fine; if not, it's an unresolved "twin".
    """

    ATTRIBUTES = ["pack_size", "variant"]
    CHECK_MIN_SIMILARITY = 0.4  # looser than pair detection: it's only a hint while typing
    CHECK_MAX_RESULTS = 5

    # --- analysing one product ----------------------------------------------------------

    @classmethod
    def analyze(cls, product, *, image_changed=True, text_changed=True) -> None:
        """Refresh the computed fields we were told are stale, then recheck the product's pairs."""
        fields = []
        if image_changed:
            fields += cls._measure_image(product)
        needs_embedding = text_changed or product.name_embedding is None
        if needs_embedding and EmbeddingService.is_enabled():
            product.name_embedding = EmbeddingService.embed(product)
            fields.append("name_embedding")
        if fields:
            # update_fields: don't overwrite anything else, or touch updated_at.
            product.save(update_fields=fields)
        cls.refresh_pairs(product)

    @staticmethod
    def _measure_image(product) -> list[str]:
        measured = {"image_phash": "", "image_width": None, "image_height": None, "blur_score": None}
        if product.image_url:
            try:
                data, _ = ImageService.fetch_url(product.image_url)
                measured = ImageService.measure(data)
            except Exception:  # a dead image link must never break saving or analysing a product
                logger.warning("could not measure image", extra={"product_id": product.id}, exc_info=True)
        for field, value in measured.items():
            setattr(product, field, value)
        return list(measured)

    # --- pairs --------------------------------------------------------------------------

    @classmethod
    def refresh_pairs(cls, product) -> None:
        candidates = cls._candidates(product)
        similar_text = EmbeddingService.similar_products(product, candidates)
        flagged = set(similar_text)

        distances = {}
        if product.image_phash:
            for other_id, other_hash in candidates.exclude(image_phash="").values_list("id", "image_phash"):
                distances[other_id] = cls.hamming(product.image_phash, other_hash)
                if distances[other_id] <= settings.LOOKALIKE_PHASH_MAX_DISTANCE:
                    flagged.add(other_id)

        # Other products not analysed yet: we can't tell if a pair went stale, so keep them all.
        if not EmbeddingService.can_compare_all(candidates):
            for other in Product.objects.filter(id__in=flagged):
                cls._save_pair(product, other, distances.get(other.id), similar_text.get(other.id))
            return

        # No longer look-alikes: forget the pair, unless a person has decided on it.
        stale = LookalikePair.objects.filter(Q(product_a=product) | Q(product_b=product), resolved_by=None)
        stale.exclude(Q(product_a__in=flagged) | Q(product_b__in=flagged)).delete()

        for other in Product.objects.filter(id__in=flagged):
            cls._save_pair(product, other, distances.get(other.id), similar_text.get(other.id))

    @staticmethod
    def _candidates(product):
        root = product.category.root()
        return Product.objects.filter(
            brand__iexact=product.brand, category_id__in=root.descendant_ids()
        ).exclude(pk=product.pk)

    @classmethod
    def _save_pair(cls, one, other, distance, similarity) -> None:
        first, second = (one, other) if one.id < other.id else (other, one)
        pair, _ = LookalikePair.objects.get_or_create(product_a=first, product_b=second)
        pair.image_distance = distance
        pair.text_similarity = similarity
        if pair.resolved_by_id is None:  # a person's decision always stands
            told_apart = bool(cls.differing_attributes(first, second))
            pair.status = LookalikePair.RESOLVED_DISTINCT if told_apart else LookalikePair.UNRESOLVED
        pair.save()

    @classmethod
    def differing_attributes(cls, first, second) -> list[str]:
        """Attributes filled in on both products with different values. A blank tells nothing apart."""
        different = []
        for attribute in cls.ATTRIBUTES:
            left = getattr(first, attribute).strip().lower()
            right = getattr(second, attribute).strip().lower()
            if left and right and left != right:
                different.append(attribute)
        return different

    @staticmethod
    def hamming(first_hash: str, second_hash: str) -> int:
        """How many of the 64 bits differ between two hex pHashes."""
        return (int(first_hash, 16) ^ int(second_hash, 16)).bit_count()

    # --- what users do ------------------------------------------------------------------

    @classmethod
    def resolve(cls, pair, status: str, user) -> LookalikePair:
        told_apart = cls.differing_attributes(pair.product_a, pair.product_b)
        if status == LookalikePair.RESOLVED_DISTINCT and not told_apart:
            # "Distinct" must be something the camera team can act on, not just a claim.
            raise ValidationError(
                {"status": ["Fill in a pack size or variant that differs on both products first."]}
            )
        pair.status = status
        pair.resolved_by = user
        pair.resolved_at = timezone.now()
        pair.save(update_fields=["status", "resolved_by", "resolved_at"])
        return pair

    @classmethod
    def find_existing(cls, name: str, brand: str, exclude_id=None):
        """Existing SKUs like the one being typed in the form. Only a warning: never blocks saving."""
        matches = Product.objects.filter(brand__iexact=brand.strip()).annotate(
            similarity=TrigramSimilarity("name", name.strip())
        )
        if exclude_id:
            matches = matches.exclude(pk=exclude_id)
        matches = matches.filter(similarity__gte=cls.CHECK_MIN_SIMILARITY)
        return matches.select_related("created_by").order_by("-similarity")[: cls.CHECK_MAX_RESULTS]
