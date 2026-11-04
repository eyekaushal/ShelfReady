from django.core.validators import URLValidator
from rest_framework import serializers


class ExtractProductRequestSerializer(serializers.Serializer):
    """POST /api/ai/extract-product/: send exactly one of `image_url` (JSON) or `image` (multipart file)."""

    image_url = serializers.CharField(
        required=False,
        max_length=500,
        validators=[URLValidator(schemes=["http", "https"], message="Enter a valid http or https URL.")],
    )
    image = serializers.FileField(required=False)

    def validate(self, attrs):
        has_url, has_file = bool(attrs.get("image_url")), bool(attrs.get("image"))
        if has_url == has_file:  # both or neither
            raise serializers.ValidationError("Send either an image URL or an image file (one of them).")
        return attrs
