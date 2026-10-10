"""Product variants (docs/product-variants.md), step 2: every batch is stock
of one variant.

Adds InventoryBatch.variant and points every existing batch at its
product's only variant (products/0008 gave each product one). 0004 then
makes the field required; that is a separate migration because PostgreSQL
will not alter a table in the same transaction that just updated its
foreign keys.
"""

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import OuterRef, Subquery


def point_batches_at_their_variant(apps, schema_editor):
    InventoryBatch = apps.get_model("inventory", "InventoryBatch")
    ProductVariant = apps.get_model("products", "ProductVariant")

    InventoryBatch.objects.filter(variant__isnull=True).update(
        variant_id=Subquery(
            ProductVariant.objects.filter(product_id=OuterRef("product_id"))
            .order_by("position", "pk")
            .values("pk")[:1]
        )
    )

    missing = list(
        InventoryBatch.objects.filter(variant__isnull=True)
        .order_by("pk")
        .values_list("batch_id", flat=True)[:50]
    )

    if missing:
        raise RuntimeError(
            "These batches' products have no variant (at most 50 shown): "
            + ", ".join(missing)
        )


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0002_inventorybatch_closed_at_inventorybatch_closed_by_and_more"),
        ("products", "0008_productvariant"),
    ]

    operations = [
        migrations.AddField(
            model_name="inventorybatch",
            name="variant",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="batches",
                to="products.productvariant",
            ),
        ),
        migrations.RunPython(
            point_batches_at_their_variant,
            migrations.RunPython.noop,
        ),
    ]
