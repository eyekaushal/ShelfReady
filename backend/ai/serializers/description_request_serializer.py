from rest_framework import serializers

from catalog.models import Category


class DescriptionRequestSerializer(serializers.Serializer):
    """POST /api/ai/generate-description/: what we know about the product so far."""

    name = serializers.CharField(min_length=2, max_length=200)
    brand = serializers.CharField(min_length=2, max_length=100)
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), required=False, allow_null=True
    )
    pack_size = serializers.CharField(max_length=50, required=False, allow_blank=True)
    variant = serializers.CharField(max_length=100, required=False, allow_blank=True)
