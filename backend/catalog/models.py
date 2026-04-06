from django.db import models
from django.urls import reverse


class ProductCategory(models.Model):
    """
    High-level grouping of products for catalog presentation.

    Examples:
    - Pick and mix candy
    - Chips

    Categories express the primary product family, not cross-cutting traits
    such as "sour" or "vegan". Those belong in tags.
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
    Cross-cutting descriptive label for products.

    Examples:
    - Sour
    - Sweet
    - Chocolate
    - Vegan
    - New

    Tags are intended for filtering and richer catalog presentation.
    They complement categories rather than replace them.
    """

    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    """
    Current product truth for the B2B catalog.

    RESPONSIBILITY:
    - represent the current live product state
    - provide metadata for browsing and ordering
    - act as source data when orders snapshot product information

    IMPORTANT BOUNDARY:
    `catalog` owns current product truth.
    `ordering` owns historical order truth.

    VISIBILITY VS ORDERABILITY:
    - `is_visible`: whether the product should be shown in the catalog UI
    - `is_orderable`: whether stores may order it right now

    These are intentionally separate because a product may still be visible
    while temporarily unavailable for ordering, for example when stock is out.

    OPTIONAL METADATA:
    - `weight_grams` is useful when weight matters, such as pick and mix candy
    - `units_per_box` is useful when packaging count matters, such as chips

    Not all product families need both fields.
    """

    code = models.PositiveIntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=200)

    description = models.TextField(blank=True)
    ingredients = models.TextField(blank=True)

    weight_grams = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Optional product weight metadata in grams.",
    )

    units_per_box = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Optional packaging metadata: number of sellable units in one box.",
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

    is_visible = models.BooleanField(
        default=True,
        help_text="Whether the product is shown in the catalog UI.",
    )
    is_orderable = models.BooleanField(
        default=True,
        help_text="Whether stores may currently order the product.",
    )

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
        Canonical public URL for this product.
        """
        return reverse("catalog:product_detail", kwargs={"product_id": self.id})
