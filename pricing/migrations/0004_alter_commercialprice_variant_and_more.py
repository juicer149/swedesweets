"""Every offer has its variant (filled in by 0003): make it required, and
keep one standard offer per variant and channel."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pricing", "0003_commercialprice_variant"),
    ]

    operations = [
        migrations.AlterField(
            model_name="commercialprice",
            name="variant",
            field=models.ForeignKey(
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="commercial_prices",
                to="products.productvariant",
            ),
        ),
        migrations.AddConstraint(
            model_name="commercialprice",
            constraint=models.UniqueConstraint(
                condition=models.Q(("batch__isnull", True)),
                fields=("variant", "channel"),
                name="unique_variant_price_per_channel",
            ),
        ),
    ]
