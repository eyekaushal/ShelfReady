from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken


class LogoutView(APIView):
    """
    POST /api/auth/logout/  {refresh} → 205

    JWTs can't be "deleted", so logout puts the refresh token on a blacklist.
    The short-lived access token expires on its own; the frontend also drops both tokens.

    AllowAny on purpose: a user whose access token already expired must still be able
    to log out. Holding the refresh token is proof enough.
    """

    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        token = request.data.get("refresh")
        if not token:
            raise serializers.ValidationError({"refresh": ["This field is required."]})

        try:
            RefreshToken(token).blacklist()
        except TokenError as exc:  # malformed, expired, or already blacklisted
            raise serializers.ValidationError({"refresh": [str(exc)]}) from exc

        return Response(status=status.HTTP_205_RESET_CONTENT)
