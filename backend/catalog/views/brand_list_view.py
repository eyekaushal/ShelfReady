from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Product


class BrandListView(APIView):
    """
    GET /api/brands/ → ["Amul", "Britannia", "Parle", ...]

    Brands are plain text on products (not a separate table), so this lists the distinct values.
    Used by the brand filter dropdown and, later, by the AI search whitelist.
    """

    permission_classes = [AllowAny]

    @extend_schema(responses={200: {"type": "array", "items": {"type": "string"}}})
    def get(self, request):
        brands = Product.objects.order_by("brand").values_list("brand", flat=True).distinct()
        return Response(list(brands))
