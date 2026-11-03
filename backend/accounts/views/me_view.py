from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from accounts.serializers.user_serializer import UserSerializer


class MeView(generics.RetrieveAPIView):
    """GET /api/auth/me/ → the logged-in user. The frontend calls this on page load."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
