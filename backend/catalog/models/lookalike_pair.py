from django.conf import settings
from django.db import models
from django.db.models import F, Q


class LookalikePair(models.Model):
    """
    Two products a shelf camera could confuse: same brand, with a similar pack photo or name.

    product_a always has the smaller id, so one pair of products can only have one row.
    resolved_by is set only when a person decided; automatic decisions leave it empty and
    can change again when the products change.
    """

    UNRESOLVED = "unresolved"  # nothing recorded tells them apart: a "twin"
    RESOLVED_DISTINCT = "resolved_distinct"  # pack size or variant differs, or a person said so
    DUPLICATE = "duplicate"  # a person says it's the same SKU listed twice
    STATUS_CHOICES = [
        (UNRESOLVED, "Unresolved"),
        (RESOLVED_DISTINCT, "Distinct"),
        (DUPLICATE, "Duplicate"),
    ]

    product_a = models.ForeignKey("catalog.Product", related_name="+", on_delete=models.CASCADE)
    product_b = models.ForeignKey("catalog.Product", related_name="+", on_delete=models.CASCADE)
    image_distance = models.PositiveSmallIntegerField(null=True, blank=True)  # pHash bits that differ, of 64
    text_similarity = models.FloatField(null=True, blank=True)  # 0 to 1
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=UNRESOLVED, db_index=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, related_name="+", on_delete=models.SET_NULL
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(fields=["product_a", "product_b"], name="unique_lookalike_pair"),
            models.CheckConstraint(condition=Q(product_a__lt=F("product_b")), name="lookalike_a_before_b"),
        ]

    def __str__(self):
        return f"{self.product_a_id} ~ {self.product_b_id} ({self.status})"
