from rest_framework import serializers

from catalog.models import Product


class ProductSummarySerializer(serializers.ModelSerializer):
    """The few fields needed to show a product next to another one."""

    created_by = serializers.CharField(source="created_by.username", read_only=True, default=None)

    class Meta:
        model = Product
        fields = ["id", "name", "brand", "pack_size", "variant", "price", "image_url", "created_by"]
        read_only_fields = fields
