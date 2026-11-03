from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.serializers.register_serializer import RegisterSerializer
from accounts.serializers.user_serializer import UserSerializer


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/  {username, email, password}
    → 201 {user, access, refresh}

    Returns tokens straight away, so the user is logged in right after signing up.
    """

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        body = {
            "user": UserSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
        return Response(body, status=status.HTTP_201_CREATED)
