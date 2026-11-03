from rest_framework import serializers

from catalog.models import Category


class CategorySerializer(serializers.ModelSerializer):
    """Used for dropdowns and for the `category_detail` block inside a product."""

    full_path = serializers.CharField(read_only=True)
    # Filled by the view with a COUNT annotation, so we don't run one query per category.
    is_leaf = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent", "full_path", "is_leaf"]

    def get_is_leaf(self, category) -> bool:
        child_count = getattr(category, "child_count", None)
        if child_count is None:  # not annotated (e.g. nested inside a product)
            return not category.children.exists()
        return child_count == 0
