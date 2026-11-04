from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q
from pgvector.django import VectorField


class Product(models.Model):
    """
    One SKU in the product master.

    Three groups of fields:
    1. Required by the brief: what a user fills in.
    2. SKU-master extras: what a shelf camera needs to tell look-alikes apart.
    3. Computed by services: never edited by users (read-only in the API).
    """

    SEARCH_FIELDS = ["name", "brand", "description"]  # what ?search= looks through

    # 1. Required by the brief
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, db_index=True)
    category = models.ForeignKey("catalog.Category", related_name="products", on_delete=models.PROTECT)
    description = models.TextField(max_length=2000)
    price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)  # Decimal: no float rounding
    image_url = models.URLField(max_length=500, blank=True)

    # 2. SKU-master extras (optional)
    gtin = models.CharField(max_length=14, blank=True, default="")  # barcode number
    pack_size = models.CharField(max_length=50, blank=True)  # "250 g"
    variant = models.CharField(max_length=100, blank=True)  # "Chocolate"
    tags = ArrayField(models.CharField(max_length=40), default=list, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        related_name="products",
        on_delete=models.SET_NULL,  # keep the product if its creator's account is deleted
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 3. Computed by services (filled from Block 10 / 11)
    image_phash = models.CharField(max_length=16, blank=True, default="")  # 64-bit hash as hex; "" = not yet
    image_width = models.PositiveIntegerField(null=True, blank=True)
    image_height = models.PositiveIntegerField(null=True, blank=True)
    blur_score = models.FloatField(null=True, blank=True)
    name_embedding = VectorField(dimensions=384, null=True, blank=True)
    readiness_score = models.PositiveSmallIntegerField(default=0)  # 0–100
    readiness_issues = models.JSONField(default=list, blank=True)
    needs_review = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # A GTIN identifies exactly one product. Empty GTINs are allowed many times,
            # so the rule only applies when a GTIN is set.
            models.UniqueConstraint(fields=["gtin"], condition=~Q(gtin=""), name="unique_gtin_when_set"),
            models.CheckConstraint(condition=Q(price__gt=0), name="price_greater_than_zero"),
        ]

    def __str__(self):
        size = f" {self.pack_size}" if self.pack_size else ""
        return f"{self.brand} {self.name}{size}"
