from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from catalog.models import Product
from catalog.permissions.is_owner_or_staff import IsOwnerOrStaff
from catalog.serializers.product_serializer import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """
    /api/products/       GET list, POST create (login needed)
    /api/products/{id}/  GET, PUT, PATCH, DELETE (owner or staff only for writes)
    """

    serializer_class = ProductSerializer
    # Check 1: logged in to write at all. Check 2: you must own the product to change it.
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrStaff]
    # Load the category (and up to two parents, for `full_path`) and creator in the same query,
    # instead of one extra query per product.
    queryset = Product.objects.select_related("category__parent__parent", "created_by")

    def perform_create(self, serializer):
        # The owner is always the logged-in user, never something sent in the request body.
        serializer.save(created_by=self.request.user)
