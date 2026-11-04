from django.db import models


class Category(models.Model):
    """
    A category in a tree, e.g. Food › Biscuits › Cream Biscuits.

    Each category points to its parent; top-level categories have no parent.
    """

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.PROTECT,  # can't delete a category that still has sub-categories
    )

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"
        constraints = [
            # "Biscuits" can exist under Food and under Pet Food, but not twice under Food.
            models.UniqueConstraint(fields=["parent", "name"], name="unique_category_name_per_parent"),
        ]

    def __str__(self):
        return self.full_path

    @property
    def full_path(self) -> str:
        """'Food › Biscuits › Cream Biscuits'. Walks up the parents."""
        names = []
        node = self
        while node is not None:
            names.append(node.name)
            node = node.parent
        return " › ".join(reversed(names))

    def descendant_ids(self) -> list[int]:
        """
        This category's id plus every sub-category below it, at any depth.
        Filtering by "Food" should also return products in "Food › Biscuits".

        One query per level of the tree (our tree is 3 levels deep, so ~3 queries).
        """
        ids = [self.id]
        current_level = [self.id]
        while current_level:
            current_level = list(
                Category.objects.filter(parent_id__in=current_level).values_list("id", flat=True)
            )
            ids.extend(current_level)
        return ids

    def root(self) -> "Category":
        """The top of this category's tree: "Food" for Food › Biscuits › Cookies."""
        node = self
        while node.parent is not None:
            node = node.parent
        return node
