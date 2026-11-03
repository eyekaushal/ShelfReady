from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    """
    GET /api/health/ → {"status": "ok"}

    Used by Render's health check and by the keep-warm GitHub Action.
    It deliberately does NOT touch the database: a ping every 10 minutes would keep
    Neon's free compute awake around the clock and use up its monthly hours.
    """

    permission_classes = [AllowAny]
    authentication_classes = []  # no login needed, and skip token parsing

    @extend_schema(responses=inline_serializer("Health", {"status": serializers.CharField()}))
    def get(self, request):
        return Response({"status": "ok"})
