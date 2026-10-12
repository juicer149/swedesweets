"""Catalog text per language, step 1: a translation also holds the
description and the ingredients, and its name may be empty (a language can
have a description before it has a name of its own)."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0008_productvariant"),
    ]

    operations = [
        migrations.AlterField(
            model_name="producttranslation",
            name="name",
            field=models.CharField(
                blank=True,
                help_text=(
                    "Full product name shown to customers in this language. "
                    "Example: Tutti Frutti Acidulé."
                ),
                max_length=160,
                verbose_name="Customer-facing name",
            ),
        ),
        migrations.AddField(
            model_name="producttranslation",
            name="description",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="producttranslation",
            name="ingredients",
            field=models.TextField(blank=True, default=""),
        ),
    ]
