"""Product variants (docs/product-variants.md), step 3: every commercial
offer is for one variant.

Adds CommercialPrice.variant and fills it in: a batch offer gets its batch's
variant (inventory/0004), any other offer its product's only variant
(products/0008). 0004 then makes it required, separately because
PostgreSQL will not alter a table in the transaction that just updated its
foreign keys.
"""

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import OuterRef, Subquery


def point_offers_at_their_variant(apps, schema_editor):
    CommercialPrice = apps.get_model("pricing", "CommercialPrice")
    InventoryBatch = apps.get_model("inventory", "InventoryBatch")
    ProductVariant = apps.get_model("products", "ProductVariant")

    CommercialPrice.objects.filter(
        variant__isnull=True,
        batch__isnull=False,
    ).update(
        variant_id=Subquery(
            InventoryBatch.objects.filter(pk=OuterRef("batch_id")).values(
                "variant_id"
            )[:1]
        )
    )

    CommercialPrice.objects.filter(
        variant__isnull=True,
        batch__isnull=True,
    ).update(
        variant_id=Subquery(
            ProductVariant.objects.filter(product_id=OuterRef("product_id"))
            .order_by("position", "pk")
            .values("pk")[:1]
        )
    )

    missing = list(
        CommercialPrice.objects.filter(variant__isnull=True)
        .order_by("pk")
        .values_list("pk", flat=True)[:50]
    )

    if missing:
        raise RuntimeError(
            "These commercial prices could not be given a variant "
            "(at most 50 shown): " + ", ".join(str(pk) for pk in missing)
        )


class Migration(migrations.Migration):

    dependencies = [
        ("pricing", "0002_create_business_standard_offers"),
        ("products", "0008_productvariant"),
        ("inventory", "0004_alter_inventorybatch_variant"),
    ]

    operations = [
        migrations.AddField(
            model_name="commercialprice",
            name="variant",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="commercial_prices",
                to="products.productvariant",
            ),
        ),
        migrations.RunPython(
            point_offers_at_their_variant,
            migrations.RunPython.noop,
        ),
    ]
