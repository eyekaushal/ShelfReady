from decimal import Decimal, InvalidOperation

from rest_framework import serializers

# Must match ProductViewSet.ordering_fields (with "-" for descending).
ALLOWED_ORDERINGS = ["price", "-price", "name", "-name", "created_at", "-created_at"]


class ParsedSearchSerializer(serializers.Serializer):
    """
    The whitelist for AI search. Claude turns a sentence into filters; this decides what we
    actually use. The LLM never touches the database: its answer only becomes query-string
    filters for the normal GET /api/products/ endpoint.

    Rules: only these keys (anything else is ignored); brand and category must exist in the
    catalog (unknown values are DROPPED, not errors); ordering must be an allowed value;
    prices must be numbers ≥ 0. Pass context={"brands": [...], "category_slugs": {...}}.
    """

    search = serializers.CharField(max_length=100, allow_blank=True, required=False, default="")
    brand = serializers.CharField(allow_blank=True, required=False, default="")
    category = serializers.CharField(allow_blank=True, required=False, default="")
    # Any JSON value is accepted here, then _price_or_none keeps it only if it's a number ≥ 0.
    min_price = serializers.JSONField(required=False, allow_null=True, default=None)
    max_price = serializers.JSONField(required=False, allow_null=True, default=None)
    ordering = serializers.CharField(allow_blank=True, required=False, default="")

    def validate_search(self, value):
        return " ".join(value.split())

    def validate_brand(self, value):
        # Match ignoring case and return the catalog's own spelling ("britannia" → "Britannia").
        by_lower = {brand.lower(): brand for brand in self.context["brands"]}
        return by_lower.get(value.strip().lower(), "")

    def validate_category(self, value):
        return value if value in self.context["category_slugs"] else ""

    def validate_min_price(self, value):
        return self._price_or_none(value)

    def validate_max_price(self, value):
        return self._price_or_none(value)

    def validate_ordering(self, value):
        return value if value in ALLOWED_ORDERINGS else ""

    def validate(self, attrs):
        low, high = attrs["min_price"], attrs["max_price"]
        if low is not None and high is not None and low > high:
            attrs["min_price"], attrs["max_price"] = high, low  # "between 50 and 20" → 20–50
        return attrs

    @staticmethod
    def _price_or_none(value):
        # Booleans are ints in Python; never treat true/false as a price.
        if value is None or isinstance(value, bool):
            return None
        try:
            price = Decimal(str(value)).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError):
            return None
        return price if price >= 0 else None
