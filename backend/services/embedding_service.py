import threading

from django.conf import settings
from django.contrib.postgres.search import TrigramSimilarity
from pgvector.django import CosineDistance


class EmbeddingService:
    """
    How similar are two products' names? There's one switch, EMBEDDINGS_ENABLED:

    - True:  a small local model turns text into 384 numbers, stored in pgvector. It understands
             meaning, but needs about 320 MB of memory to load.
    - False: pg_trgm compares shared letter groups inside Postgres, using no app memory.
             Render's free plan (512 MB) uses this.

    Pack size is left out of the text on purpose: "Parle-G 90 g" and "Parle-G 250 g" must score
    as look-alikes, because the camera sees almost the same pack.
    """

    MODEL_NAME = "BAAI/bge-small-en-v1.5"
    _model = None
    _lock = threading.Lock()  # gunicorn threads must not load the model twice

    @staticmethod
    def is_enabled() -> bool:
        return settings.EMBEDDINGS_ENABLED

    @classmethod
    def embed(cls, product) -> list[float] | None:
        """The product's embedding, or None when embeddings are off."""
        if not cls.is_enabled():
            return None
        text = " ".join(part for part in [product.brand, product.name, product.variant] if part)
        return [float(number) for number in next(iter(cls._load_model().embed([text])))]

    @classmethod
    def similar_products(cls, product, candidates) -> dict[int, float]:
        """{product id: similarity} for the candidates that pass the threshold."""
        if cls.is_enabled():
            if product.name_embedding is None:
                return {}
            scored = candidates.filter(name_embedding__isnull=False).annotate(
                distance=CosineDistance("name_embedding", product.name_embedding)
            )
            scores = {row.id: 1 - row.distance for row in scored}
            threshold = settings.LOOKALIKE_TEXT_MIN_SIMILARITY
        else:
            scored = candidates.annotate(similarity=TrigramSimilarity("name", product.name))
            scores = {row.id: row.similarity for row in scored}
            threshold = settings.LOOKALIKE_TRIGRAM_MIN_SIMILARITY
        return {product_id: round(score, 3) for product_id, score in scores.items() if score >= threshold}

    @classmethod
    def can_compare_all(cls, candidates) -> bool:
        """False when embeddings are on but some candidates don't have one yet."""
        return not cls.is_enabled() or not candidates.filter(name_embedding__isnull=True).exists()

    @classmethod
    def _load_model(cls):
        # Loaded on first use and imported here, so servers with embeddings off never pay for it.
        with cls._lock:
            if cls._model is None:
                from fastembed import TextEmbedding

                cls._model = TextEmbedding(cls.MODEL_NAME)
        return cls._model
