from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from ai.serializers.search_request_serializer import SearchRequestSerializer
from common.throttling.global_ai_throttle import GlobalAiThrottle
from services.nl_search_service import NLSearchService


class ParseSearchView(APIView):
    """
    POST /api/ai/parse-search/  {"query": "..."} → {"filters": {...}, "cached": bool}

    Open to everyone, like the catalog itself, but rate limited per user / IP. The returned
    filters are meant for GET /api/products/; this endpoint never queries products itself.
    """

    permission_classes = [AllowAny]
    throttle_scope = "ai_search"
    throttle_classes = [ScopedRateThrottle, GlobalAiThrottle]

    @extend_schema(
        tags=["ai"],
        request=SearchRequestSerializer,
        responses={
            200: inline_serializer(
                "ParsedSearch",
                {
                    "filters": inline_serializer(
                        "SearchFilters",
                        {
                            "search": serializers.CharField(),
                            "brand": serializers.CharField(),
                            "category": serializers.CharField(),
                            "min_price": serializers.FloatField(allow_null=True),
                            "max_price": serializers.FloatField(allow_null=True),
                            "ordering": serializers.CharField(),
                        },
                    ),
                    "cached": serializers.BooleanField(),
                },
            ),
            503: OpenApiResponse(description="AI not configured or busy: fall back to keyword search."),
        },
        examples=[
            OpenApiExample(
                "Request", value={"query": "Britannia biscuits under ₹50, cheapest first"}, request_only=True
            ),
            OpenApiExample(
                "Response",
                value={
                    "filters": {
                        "search": "",
                        "brand": "Britannia",
                        "category": "biscuits",
                        "min_price": None,
                        "max_price": 50.0,
                        "ordering": "price",
                    },
                    "cached": False,
                },
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = SearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        filters, cached = NLSearchService().parse(serializer.validated_data["query"])
        return Response({"filters": filters, "cached": cached})
