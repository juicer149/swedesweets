"""Product variants (docs/product-variants.md), step 4: every order line is
for one variant, its offer's.

Adds OrderLine.variant and fills it in from each line's offer (pricing/0004
gave every offer its variant). 0017 then makes it required, separately
because PostgreSQL will not alter a table in the transaction that just
updated its foreign keys.
"""

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import OuterRef, Subquery


def point_lines_at_their_variant(apps, schema_editor):
    OrderLine = apps.get_model("orders", "OrderLine")
    CommercialPrice = apps.get_model("pricing", "CommercialPrice")

    OrderLine.objects.filter(variant__isnull=True).update(
        variant_id=Subquery(
            CommercialPrice.objects.filter(
                pk=OuterRef("commercial_offer_id")
            ).values("variant_id")[:1]
        )
    )

    missing = list(
        OrderLine.objects.filter(variant__isnull=True)
        .order_by("pk")
        .values_list("pk", flat=True)[:50]
    )

    if missing:
        raise RuntimeError(
            "These order lines could not be given a variant "
            "(at most 50 shown): " + ", ".join(str(pk) for pk in missing)
        )


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0015_remove_orderline_quantity_and_unit"),
        ("pricing", "0004_alter_commercialprice_variant_and_more"),
        ("products", "0008_productvariant"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderline",
            name="variant",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="order_lines",
                to="products.productvariant",
            ),
        ),
        migrations.RunPython(
            point_lines_at_their_variant,
            migrations.RunPython.noop,
        ),
    ]
