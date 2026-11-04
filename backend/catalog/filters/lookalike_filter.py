import django_filters
from django.db.models import Q

from catalog.models import LookalikePair


class LookalikeFilter(django_filters.FilterSet):
    """?status=unresolved&product=12 (pairs that include product 12, on either side)"""

    status = django_filters.ChoiceFilter(choices=LookalikePair.STATUS_CHOICES)
    product = django_filters.NumberFilter(method="filter_product")

    class Meta:
        model = LookalikePair
        fields = ["status", "product"]

    def filter_product(self, queryset, name, value):
        return queryset.filter(Q(product_a=value) | Q(product_b=value))
