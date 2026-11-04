from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from catalog.filters.lookalike_filter import LookalikeFilter
from catalog.models import LookalikePair
from catalog.serializers.lookalike_pair_serializer import LookalikePairSerializer
from catalog.serializers.product_summary_serializer import ProductSummarySerializer
from catalog.serializers.resolve_lookalike_serializer import ResolveLookalikeSerializer
from services.lookalike_service import LookalikeService


class LookalikeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET  /api/lookalikes/?status=unresolved&product=12   pairs a camera could confuse
    POST /api/lookalikes/{id}/resolve/                   mark as distinct or duplicate
    GET  /api/lookalikes/check/?name=...&brand=...       similar SKUs, for the Add Product warning
    """

    serializer_class = LookalikePairSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = LookalikeFilter
    queryset = LookalikePair.objects.select_related(
        "product_a__created_by", "product_b__created_by", "resolved_by"
    )

    @extend_schema(request=ResolveLookalikeSerializer, responses=LookalikePairSerializer)
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def resolve(self, request, pk=None):
        # Any logged-in user may review a pair: it only records a decision. Changing the
        # products themselves stays limited to their creator or staff.
        pair = self.get_object()

        serializer = ResolveLookalikeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pair = LookalikeService.resolve(pair, serializer.validated_data["status"], request.user)
        return Response(LookalikePairSerializer(pair).data)

    @extend_schema(
        parameters=[
            OpenApiParameter("name", str, required=True),
            OpenApiParameter("brand", str, required=True),
            OpenApiParameter("exclude", int, description="Product id to leave out (when editing)."),
        ],
        responses=ProductSummarySerializer(many=True),
    )
    @action(detail=False, methods=["get"], pagination_class=None, filter_backends=[])
    def check(self, request):
        name = request.query_params.get("name", "").strip()
        brand = request.query_params.get("brand", "").strip()
        exclude = request.query_params.get("exclude", "")
        if not name or not brand:
            raise ValidationError({"name": ["Send both name and brand."]})
        if exclude and not exclude.isdigit():
            raise ValidationError({"exclude": ["Must be a product id."]})

        matches = LookalikeService.find_existing(name, brand, exclude_id=exclude or None)
        return Response(ProductSummarySerializer(matches, many=True).data)
