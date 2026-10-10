"""Every order line has its variant (filled in by 0016): make it required."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0016_orderline_variant"),
    ]

    operations = [
        migrations.AlterField(
            model_name="orderline",
            name="variant",
            field=models.ForeignKey(
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="order_lines",
                to="products.productvariant",
            ),
        ),
    ]
