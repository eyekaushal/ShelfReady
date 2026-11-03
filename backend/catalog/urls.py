from django.urls import path
from rest_framework.routers import DefaultRouter

from catalog.views.brand_list_view import BrandListView
from catalog.views.category_viewset import CategoryViewSet
from catalog.views.product_viewset import ProductViewSet

# The router creates the list + detail URLs for each ViewSet.
router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("categories", CategoryViewSet, basename="category")

urlpatterns = [
    path("brands/", BrandListView.as_view(), name="brand-list"),
    *router.urls,
]
