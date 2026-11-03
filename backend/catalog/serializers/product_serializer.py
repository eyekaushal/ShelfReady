from decimal import Decimal

from django.core.validators import URLValidator
from rest_framework import serializers

from catalog.models import Category, Product
from services.gtin_validator import GtinValidator


class ProductSerializer(serializers.ModelSerializer):
    """
    Validates product input and shapes product JSON.

    Writes take `category` as an id; reads also include `category_detail`
    (name + full path) so the frontend doesn't need a second request.
    """

    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    category_detail = serializers.SerializerMethodField()
    created_by = serializers.CharField(source="created_by.username", read_only=True, default=None)

    name = serializers.CharField(min_length=2, max_length=200)
    brand = serializers.CharField(min_length=2, max_length=100)
    description = serializers.CharField(max_length=2000)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    image_url = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        # Only http/https. Django's default would also allow ftp:// links.
        validators=[URLValidator(schemes=["http", "https"], message="Enter a valid http or https URL.")],
    )
    gtin = serializers.CharField(max_length=20, required=False, allow_blank=True)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=40), required=False, max_length=10
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "brand",
            "category",
            "category_detail",
            "description",
            "price",
            "image_url",
            "gtin",
            "pack_size",
            "variant",
            "tags",
            "created_by",
            "created_at",
            "updated_at",
            "readiness_score",
            "readiness_issues",
            "needs_review",
        ]
        # Computed by services, never set by users.
        read_only_fields = ["readiness_score", "readiness_issues", "needs_review"]
        # The DB constraints are our safety net; validate_gtin / validate_price give friendly messages,
        # so turn off DRF's auto-generated validators for them (they'd duplicate the errors).
        validators = []

    def get_category_detail(self, product) -> dict:
        category = product.category
        return {"id": category.id, "name": category.name, "full_path": category.full_path}

    # --- field rules (DRF calls validate_<field> automatically) ---

    def validate_name(self, value):
        return self._clean_text(value)

    def validate_brand(self, value):
        return self._clean_text(value)

    def validate_description(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("This field may not be blank.")
        return value

    def validate_price(self, value: Decimal):
        if value <= 0:
            raise serializers.ValidationError("Must be greater than 0.")
        return value

    def validate_gtin(self, value):
        gtin = value.replace(" ", "").replace("-", "")  # people paste "8901 0630 1057 4"
        if not gtin:
            return ""

        error = GtinValidator.error_for(gtin)
        if error:
            raise serializers.ValidationError(error)

        duplicates = Product.objects.filter(gtin=gtin)
        if self.instance is not None:  # on update, don't clash with ourselves
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError("A product with this GTIN already exists.")
        return gtin

    def validate_tags(self, values):
        # Lower-case, trimmed, no blanks, no repeats, original order kept.
        cleaned = [value.strip().lower() for value in values if value.strip()]
        return list(dict.fromkeys(cleaned))

    @staticmethod
    def _clean_text(value: str) -> str:
        # "  Parle   G " → "Parle G", so search and duplicate checks aren't fooled by spaces.
        return " ".join(value.split())
