"""Every batch has its variant (filled in by 0003): make it required."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0003_inventorybatch_variant"),
    ]

    operations = [
        migrations.AlterField(
            model_name="inventorybatch",
            name="variant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="batches",
                to="products.productvariant",
            ),
        ),
    ]
