"""Prices per variant: a product with several variants has a standard
offer per variant and channel, so the one-per-product rule goes
(unique_variant_price_per_channel stays)."""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("pricing", "0004_alter_commercialprice_variant_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="commercialprice",
            name="unique_product_price_per_channel",
        ),
    ]
