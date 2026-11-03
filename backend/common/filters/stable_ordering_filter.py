from rest_framework.filters import OrderingFilter


class StableOrderingFilter(OrderingFilter):
    """
    OrderingFilter that always adds `id` as a final tie-breaker.

    Why: many products share a price. Without a tie-breaker, Postgres may return
    equal-price rows in a different order on each query, so a product can show up
    on page 1 AND page 2 (or on neither) while paging.
    """

    def get_ordering(self, request, queryset, view):
        ordering = list(super().get_ordering(request, queryset, view) or [])
        if not any(field.lstrip("-") == "id" for field in ordering):
            ordering.append("-id")
        return ordering
