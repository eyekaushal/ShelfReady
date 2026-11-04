from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from services.claude_client import ClaudeClient


class AIStatusView(APIView):
    """GET /api/ai/status/ → {"enabled": true}. The frontend hides or disables AI buttons when false."""

    permission_classes = [AllowAny]

    @extend_schema(responses=inline_serializer("AIStatus", {"enabled": serializers.BooleanField()}))
    def get(self, request):
        return Response({"enabled": ClaudeClient.is_configured()})
