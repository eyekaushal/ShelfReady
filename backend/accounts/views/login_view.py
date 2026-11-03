from rest_framework_simplejwt.views import TokenObtainPairView


class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/  {username, password} → 200 {access, refresh}

    simplejwt does the work; we only add rate limiting against password guessing.
    """

    throttle_scope = "auth"
