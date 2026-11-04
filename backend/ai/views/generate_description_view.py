from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ai.serializers.description_request_serializer import DescriptionRequestSerializer
from ai.serializers.generated_description_serializer import GeneratedDescriptionSerializer
from services.description_service import DescriptionService


class GenerateDescriptionView(APIView):
    """POST /api/ai/generate-description/: name + brand (+ category, pack size, variant) → text + tags."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "ai"

    @extend_schema(
        tags=["ai"],
        request=DescriptionRequestSerializer,
        responses={
            200: GeneratedDescriptionSerializer,
            503: OpenApiResponse(description="AI not configured or busy (ai_not_configured / ai_busy)."),
        },
        examples=[
            OpenApiExample(
                "Request",
                value={
                    "name": "Good Day Cashew Cookies",
                    "brand": "Britannia",
                    "category": 5,
                    "pack_size": "200 g",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Response",
                value={
                    "description": "Crunchy cookies with cashew pieces from Britannia's Good Day range. "
                    "Sold in a 200 g pack.",
                    "tags": ["cookies", "cashew", "biscuits"],
                },
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = DescriptionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(DescriptionService().generate(**serializer.validated_data))
