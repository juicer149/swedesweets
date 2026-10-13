"""Order lines keep a copy of what was bought (docs/roadmap.md): its name with
the size, SKU, variant label, weight and stock unit, so an old order reads
the same however the product changes later.

Adds the fields and fills them in for the lines there are, from each line's
variant and product as they are now: the best there is for orders placed
before the copy was kept. New lines take theirs when first saved
(OrderLine.snapshot_variant).
"""

from django.db import migrations, models

# products.catalog.VARIANT_NAME_SEPARATOR, as it is today (a migration does
# not import the code it might outlive).
SEPARATOR = " — "


def _display_name(*, brand: str, name: str, label: str) -> str:
    product_name = SEPARATOR.join(part for part in (brand, name) if part)

    return f"{product_name}{SEPARATOR}{label}" if label else product_name


def copy_what_was_bought(apps, schema_editor):
    OrderLine = apps.get_model("orders", "OrderLine")

    lines = OrderLine.objects.filter(name_snapshot="").select_related(
        "variant",
        "variant__product",
    )

    for line in lines.iterator(chunk_size=500):
        variant = line.variant
        product = variant.product

        line.name_snapshot = _display_name(
            brand=product.brand,
            name=product.name,
            label=variant.label,
        )
        line.sku_snapshot = variant.sku
        line.variant_label_snapshot = variant.label
        line.weight_per_unit_snapshot = variant.weight_per_unit
        line.stock_unit_snapshot = product.stock_unit
        line.save(
            update_fields=[
                "name_snapshot",
                "sku_snapshot",
                "variant_label_snapshot",
                "weight_per_unit_snapshot",
                "stock_unit_snapshot",
            ]
        )


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0017_alter_orderline_variant"),
        ("products", "0008_productvariant"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderline",
            name="name_snapshot",
            field=models.CharField(blank=True, default="", max_length=400),
        ),
        migrations.AddField(
            model_name="orderline",
            name="sku_snapshot",
            field=models.CharField(blank=True, default="", max_length=180),
        ),
        migrations.AddField(
            model_name="orderline",
            name="variant_label_snapshot",
            field=models.CharField(blank=True, default="", max_length=40),
        ),
        migrations.AddField(
            model_name="orderline",
            name="weight_per_unit_snapshot",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="orderline",
            name="stock_unit_snapshot",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.RunPython(
            copy_what_was_bought,
            migrations.RunPython.noop,
        ),
    ]
