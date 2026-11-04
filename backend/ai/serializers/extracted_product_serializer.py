from rest_framework import serializers

CONFIDENCE_LEVELS = ["high", "medium", "low"]
CONFIDENCE_FIELDS = ["name", "brand", "category", "variant", "pack_size", "description", "tags"]


class ExtractedProductSerializer(serializers.Serializer):
    """
    Validates Claude's answer for photo → product. Even with a JSON schema, the model's output
    is untrusted data: we re-check lengths, the category whitelist and the confidence values
    with the same limits as ProductSerializer.

    Pass the allowed category slugs as context={"category_slugs": {...}}.
    """

    name = serializers.CharField(max_length=200, allow_blank=True)
    brand = serializers.CharField(max_length=100, allow_blank=True)
    category_slug = serializers.CharField(allow_blank=True)
    variant = serializers.CharField(max_length=100, allow_blank=True)
    pack_size = serializers.CharField(max_length=50, allow_blank=True)
    description = serializers.CharField(max_length=300, allow_blank=True)  # 1-2 short sentences
    tags = serializers.ListField(child=serializers.CharField(max_length=40), max_length=10)
    confidence = serializers.DictField(child=serializers.ChoiceField(choices=CONFIDENCE_LEVELS))
    notes = serializers.CharField(max_length=500, allow_blank=True)

    def validate_category_slug(self, value):
        # "none" or an unknown slug → empty, so the user picks a category themselves.
        return value if value in self.context["category_slugs"] else ""

    def validate_tags(self, values):
        cleaned = [value.strip().lower() for value in values if value.strip()]
        return list(dict.fromkeys(cleaned))[:6]

    def validate_confidence(self, value):
        # Keep only the fields we know; anything missing counts as "low".
        return {field: value.get(field, "low") for field in CONFIDENCE_FIELDS}
