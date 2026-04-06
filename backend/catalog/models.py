from django.db import models
from django.urls import reverse


class ProductCategory(models.Model):
    """
    High-level grouping of products for UI presentation.

    Used to organize products into sections (e.g. "Candy", "Chips").
    """

    name = models.CharField(max_length=100, unique=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "Product categories"

    def __str__(self) -> str:
        return self.name


class ProductTag(models.Model):
    """
    Flexible labels for products (e.g. "Sour", "Vegan", "New").

    Used for filtering, metadata, and future UI enhancements.
    """

    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    """
    Product in the B2B catalog used for store ordering.

    Managed via admin and acts as the source of truth for available items.

    Orders store snapshots (code/name) to preserve history.
    Additional optional metadata (weight, units per box) is used for
    better product understanding in the UI.
    """

    code = models.PositiveIntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=200)

    description = models.TextField(blank=True)
    ingredients = models.TextField(blank=True)

    weight_grams = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Weight per unit in grams",
    )

    units_per_box = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of units per box",
    )

    category = models.ForeignKey(
        ProductCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
    )

    tags = models.ManyToManyField(
        ProductTag,
        blank=True,
        related_name="products",
    )

    is_active = models.BooleanField(default=True)

    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["category__sort_order", "category__name", "code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"

    def get_absolute_url(self) -> str:
        """
        Canonical URL for this product.

        Keeps routing logic out of templates and avoids hardcoded paths.
        """
        return reverse("catalog:product_detail", kwargs={"product_id": self.id})
