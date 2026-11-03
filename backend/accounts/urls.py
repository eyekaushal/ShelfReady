from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views.login_view import LoginView
from accounts.views.logout_view import LogoutView
from accounts.views.me_view import MeView
from accounts.views.register_view import RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
]
