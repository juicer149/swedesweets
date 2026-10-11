from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0008_productvariant"),
    ]

    operations = [
        migrations.AddField(
            model_name="productvariant",
            name="name",
            field=models.CharField(
                blank=True,
                help_text='"Small", "Large bar"; optional, the label is used without it.',
                max_length=80,
            ),
        ),
    ]
