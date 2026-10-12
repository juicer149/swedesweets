"""Catalog text per language, step 3: the profile no longer holds the
description and ingredients (they are in the translations since 0010)."""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0010_move_catalog_text_to_french"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="productprofile",
            name="description",
        ),
        migrations.RemoveField(
            model_name="productprofile",
            name="ingredients",
        ),
    ]
