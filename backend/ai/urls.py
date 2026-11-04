from django.urls import path

from ai.views.ai_status_view import AIStatusView
from ai.views.extract_product_view import ExtractProductView
from ai.views.generate_description_view import GenerateDescriptionView
from ai.views.parse_search_view import ParseSearchView

urlpatterns = [
    path("status/", AIStatusView.as_view(), name="ai-status"),
    path("extract-product/", ExtractProductView.as_view(), name="ai-extract-product"),
    path("generate-description/", GenerateDescriptionView.as_view(), name="ai-generate-description"),
    path("parse-search/", ParseSearchView.as_view(), name="ai-parse-search"),
]
