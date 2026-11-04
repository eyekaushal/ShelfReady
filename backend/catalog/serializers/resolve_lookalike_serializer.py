from rest_framework import serializers

from catalog.models import LookalikePair


class ResolveLookalikeSerializer(serializers.Serializer):
    """POST /api/lookalikes/{id}/resolve/  {"status": "resolved_distinct" | "duplicate"}"""

    status = serializers.ChoiceField(choices=[LookalikePair.RESOLVED_DISTINCT, LookalikePair.DUPLICATE])
