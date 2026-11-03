# Django loads `catalog.admin` on startup; importing these registers the admin pages.
from catalog.admin.category_admin import CategoryAdmin
from catalog.admin.product_admin import ProductAdmin

__all__ = ["CategoryAdmin", "ProductAdmin"]
