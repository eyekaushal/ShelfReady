from django.contrib import admin

from catalog.models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["full_path", "slug"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
