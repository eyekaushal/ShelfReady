import django_filters
from rest_framework.exceptions import ValidationError

from catalog.models import Category, Product


class ProductFilter(django_filters.FilterSet):
    """
    ?brand=Parle&category=biscuits&min_price=10&max_price=50

    - brand: exact match, ignoring case ("parle" finds "Parle")
    - category: a category slug; includes all of its sub-categories
    - min_price / max_price: inclusive price range
    """

    brand = django_filters.CharFilter(field_name="brand", lookup_expr="iexact")
    category = django_filters.CharFilter(method="filter_category")
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    class Meta:
        model = Product
        fields = ["brand", "category", "min_price", "max_price"]

    def filter_category(self, queryset, name, value):
        category = Category.objects.filter(slug=value).first()
        if category is None:
            # Unknown slug (e.g. an old shared link): show "no results", not an error page.
            return queryset.none()
        return queryset.filter(category_id__in=category.descendant_ids())

    def filter_queryset(self, queryset):
        # Runs after each value is parsed, so prices here are real numbers.
        min_price = self.form.cleaned_data.get("min_price")
        max_price = self.form.cleaned_data.get("max_price")
        if min_price is not None and max_price is not None and min_price > max_price:
            raise ValidationError({"min_price": ["Must be less than or equal to max_price."]})
        return super().filter_queryset(queryset)
