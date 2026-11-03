from django.contrib import admin

from catalog.models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "brand", "pack_size", "price", "category", "readiness_score", "created_by"]
    list_filter = ["brand", "needs_review"]
    search_fields = ["name", "brand", "gtin"]
    # Computed fields: shown but not editable.
    readonly_fields = [
        "image_phash", "image_width", "image_height", "blur_score",
        "readiness_score", "readiness_issues", "created_at", "updated_at",
    ]
    exclude = ["name_embedding"]  # 384 numbers, not useful to look at
