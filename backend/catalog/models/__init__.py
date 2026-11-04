# Django looks for models in `catalog.models`, so import each model class here.
from catalog.models.category import Category
from catalog.models.lookalike_pair import LookalikePair
from catalog.models.product import Product

__all__ = ["Category", "LookalikePair", "Product"]
