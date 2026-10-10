"""Product variants (docs/product-variants.md), step 1: the model, and one
variant for every product that exists.

Each product gets its only variant: no label, position 1, the product's
SKU and weight, active. Nothing points at variants yet (batches, prices
and order lines move over in the next steps), so the site works as before.
"""

import django.db.models.deletion
import django.db.models.functions.text
from django.db import migrations, models


def create_only_variants(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    ProductVariant = apps.get_model("products", "ProductVariant")

    products_without_variant = (
        Product.objects.filter(variants__isnull=True)
        .order_by("pk")
        .values_list("pk", "sku", "weight_per_unit")
    )

    ProductVariant.objects.bulk_create(
        [
            ProductVariant(
                product_id=product_id,
                label="",
                position=1,
                sku=sku,
                weight_per_unit=weight_per_unit,
                active=True,
            )
            for product_id, sku, weight_per_unit in products_without_variant
        ],
        batch_size=500,
    )

    products = Product.objects.count()
    variants = ProductVariant.objects.count()

    if products != variants:
        raise RuntimeError(
            f"Expected one variant per product: {products} products, "
            f"{variants} variants."
        )


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0007_productprofile_display"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductVariant",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "label",
                    models.CharField(
                        blank=True,
                        help_text="\"M\", \"60 g\"; empty for a product's only variant.",
                        max_length=40,
                    ),
                ),
                (
                    "position",
                    models.PositiveSmallIntegerField(
                        default=1,
                        help_text="Order shown everywhere (1, 2, 3 …).",
                    ),
                ),
                (
                    "sku",
                    models.CharField(
                        editable=False,
                        max_length=180,
                        unique=True,
                    ),
                ),
                (
                    "weight_per_unit",
                    models.PositiveIntegerField(
                        help_text="Weight in grams for one physical stock unit.",
                    ),
                ),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="variants",
                        to="products.product",
                    ),
                ),
            ],
            options={
                "ordering": ["product_id", "position", "id"],
                "constraints": [
                    models.UniqueConstraint(
                        models.F("product"),
                        django.db.models.functions.text.Lower("label"),
                        name="unique_variant_label_per_product",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(position__gte=1),
                        name="variant_position_at_least_1",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(weight_per_unit__gte=1),
                        name="variant_weight_per_unit_at_least_min",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(weight_per_unit__lte=50000),
                        name="variant_weight_per_unit_at_most_max",
                    ),
                ],
            },
        ),
        migrations.RunPython(
            create_only_variants,
            migrations.RunPython.noop,
        ),
    ]
