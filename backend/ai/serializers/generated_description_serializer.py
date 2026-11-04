from rest_framework import serializers


class GeneratedDescriptionSerializer(serializers.Serializer):
    """Validates Claude's answer for the description generator (output is untrusted data)."""

    # Short on purpose: what the product is, not how the pack looks (see DescriptionService prompt).
    description = serializers.CharField(min_length=20, max_length=300)
    tags = serializers.ListField(child=serializers.CharField(max_length=40), max_length=10)

    def validate_tags(self, values):
        cleaned = [value.strip().lower() for value in values if value.strip()]
        return list(dict.fromkeys(cleaned))[:6]
