from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from catalog.filters.product_filter import ProductFilter
from catalog.models import Product
from catalog.permissions.is_owner_or_staff import IsOwnerOrStaff
from catalog.serializers.product_serializer import ProductSerializer
from catalog.tasks import analyze_product
from common.filters.stable_ordering_filter import StableOrderingFilter


class ProductViewSet(viewsets.ModelViewSet):
    """
    /api/products/       GET list, POST create (login needed)
    /api/products/{id}/  GET, PUT, PATCH, DELETE (owner or staff only for writes)

    List query params (all optional, all combinable):
      ?search=good day          case-insensitive, in name / brand / description
      ?brand=Britannia          ?category=biscuits (includes sub-categories)
      ?min_price=10&max_price=50
      ?ordering=price | -price | name | -name | created_at | -created_at
      ?page=2&page_size=24
    """

    serializer_class = ProductSerializer
    # Check 1: logged in to write at all. Check 2: you must own the product to change it.
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrStaff]
    # Load the category (and up to two parents, for `full_path`) and creator in the same query,
    # instead of one extra query per product.
    queryset = Product.objects.select_related("category__parent__parent", "created_by")

    filter_backends = [DjangoFilterBackend, SearchFilter, StableOrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["name", "brand", "description"]  # icontains on each, OR-ed together
    ordering_fields = ["price", "name", "created_at"]
    ordering = ["-created_at"]  # newest first by default

    def perform_create(self, serializer):
        # The owner is always the logged-in user, never something sent in the request body.
        product = serializer.save(created_by=self.request.user)
        analyze_product.delay(product.id)

    def perform_update(self, serializer):
        before = serializer.instance
        old_image = before.image_url
        old_text = (before.name, before.brand, before.variant)

        product = serializer.save()

        # Only redo what's stale. The pairs are always rechecked, because a new pack size
        # or a new category can change them.
        analyze_product.delay(
            product.id,
            image_changed=product.image_url != old_image,
            text_changed=(product.name, product.brand, product.variant) != old_text,
        )
