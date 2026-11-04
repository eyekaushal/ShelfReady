from rest_framework import serializers


class SearchRequestSerializer(serializers.Serializer):
    """POST /api/ai/parse-search/  {"query": "Britannia biscuits under ₹50, cheapest first"}"""

    query = serializers.CharField(min_length=2, max_length=200)

    def validate_query(self, value):
        return " ".join(value.split())
