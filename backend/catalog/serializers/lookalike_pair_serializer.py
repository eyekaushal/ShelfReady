from rest_framework import serializers

from catalog.models import LookalikePair
from catalog.serializers.product_summary_serializer import ProductSummarySerializer
from services.lookalike_service import LookalikeService


class LookalikePairSerializer(serializers.ModelSerializer):
    product_a = ProductSummarySerializer(read_only=True)
    product_b = ProductSummarySerializer(read_only=True)
    resolved_by = serializers.CharField(source="resolved_by.username", read_only=True, default=None)
    differing_attributes = serializers.SerializerMethodField()

    class Meta:
        model = LookalikePair
        fields = [
            "id",
            "product_a",
            "product_b",
            "image_distance",
            "text_similarity",
            "status",
            "differing_attributes",
            "resolved_by",
            "resolved_at",
        ]
        read_only_fields = fields

    def get_differing_attributes(self, pair) -> list[str]:
        return LookalikeService.differing_attributes(pair.product_a, pair.product_b)
