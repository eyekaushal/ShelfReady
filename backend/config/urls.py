from django.contrib import admin
from django.urls import include, path

from common.views.error_views import ErrorViews
from common.views.health_view import HealthView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", HealthView.as_view(), name="health"),
    path("api/auth/", include("accounts.urls")),
]

# Used only when DEBUG=False (in DEBUG, Django shows its own debug pages).
handler404 = ErrorViews.not_found
handler500 = ErrorViews.server_error
