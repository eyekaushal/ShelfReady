from django.db.models import Count
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from catalog.models import Category
from catalog.serializers.category_serializer import CategorySerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/categories/ → every category with its full path (for dropdowns).

    Read-only: categories are managed in Django admin, not by catalog users.
    Not paginated, because the list is small and a dropdown needs all of it.
    """

    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None
    queryset = Category.objects.select_related("parent__parent").annotate(child_count=Count("children"))
