from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ai.serializers.extract_product_request_serializer import ExtractProductRequestSerializer
from services.ai_service_error import AIServiceError
from services.claude_client import ClaudeClient
from services.image_service import ImageService
from services.product_extract_service import ProductExtractService

EXAMPLE_RESPONSE = {
    "fields": {
        "name": "Good Day Cashew Cookies",
        "brand": "Britannia",
        "category": 5,
        "variant": "Cashew",
        "pack_size": "200 g",
        "description": "Crunchy cookies with cashew pieces from Britannia's Good Day range, in a 200 g pack.",
        "tags": ["cookies", "cashew", "biscuits", "tea time"],
    },
    "confidence": {
        "name": "high",
        "brand": "high",
        "category": "high",
        "variant": "high",
        "pack_size": "medium",
        "description": "medium",
        "tags": "medium",
    },
    "notes": "Net weight is partly hidden by a fold; read as 200 g.",
}


class ExtractProductView(APIView):
    """
    POST /api/ai/extract-product/  → suggested product fields read from a pack photo.

    Send JSON {"image_url": "https://..."} or multipart with an `image` file (≤ 5 MB, JPEG/PNG/WebP).
    Nothing is saved: the frontend prefills the form and the user reviews before saving.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    throttle_scope = "ai"

    @extend_schema(
        tags=["ai"],
        request={
            "application/json": ExtractProductRequestSerializer,
            "multipart/form-data": ExtractProductRequestSerializer,
        },
        responses={
            200: inline_serializer(
                "ExtractedProduct",
                {
                    "fields": serializers.DictField(),
                    "confidence": serializers.DictField(child=serializers.CharField()),
                    "notes": serializers.CharField(),
                },
            ),
            400: OpenApiResponse(description="Bad image URL / file (validation_error)."),
            502: OpenApiResponse(description="AI answer failed validation twice (ai_invalid_output)."),
            503: OpenApiResponse(description="AI not configured or busy (ai_not_configured / ai_busy)."),
        },
        examples=[
            OpenApiExample(
                "From an image URL",
                value={"image_url": "https://images.example.com/good-day.jpg"},
                request_only=True,
            ),
            OpenApiExample("Suggested fields", value=EXAMPLE_RESPONSE, response_only=True),
        ],
    )
    def post(self, request):
        # Fail fast: don't download an image we can't send anywhere.
        if not ClaudeClient.is_configured():
            raise AIServiceError("ai_not_configured", "AI features are not set up on this server.")

        serializer = ExtractProductRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data.get("image_url"):
            image_bytes, media_type = ImageService.fetch_url(serializer.validated_data["image_url"])
        else:
            image_bytes, media_type = ImageService.read_upload(serializer.validated_data["image"])

        return Response(ProductExtractService().extract(image_bytes, media_type))
