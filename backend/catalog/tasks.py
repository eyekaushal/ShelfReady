import logging

from celery import shared_task

from catalog.models import Product
from services.lookalike_service import LookalikeService

logger = logging.getLogger("shelfready.lookalikes")


@shared_task
def analyze_product(product_id: int, image_changed: bool = True, text_changed: bool = True) -> None:
    """
    Background work after a product is saved. A Redis worker runs this locally; on Render
    CELERY_TASK_ALWAYS_EAGER runs the same code inline.
    """
    product = Product.objects.select_related("category").filter(pk=product_id).first()
    if product is None:  # deleted before the worker got to it
        return
    try:
        LookalikeService.analyze(product, image_changed=image_changed, text_changed=text_changed)
    except Exception:  # an add-on must never make saving a product fail
        logger.exception("product analysis failed", extra={"product_id": product_id})
