"""Catalog text per language, step 2: the description and ingredients
written so far are French, so they move from the product's profile to its
French translation (made, with no name, where the product has none).

Backwards, the French text goes back to the profile and the translations
without a name are removed (a name was required before). Text in other
languages has nowhere to go back to and is lost.
"""

from django.db import migrations

FRENCH = "fr"


def move_text_to_french(apps, schema_editor):
    ProductProfile = apps.get_model("products", "ProductProfile")
    ProductTranslation = apps.get_model("products", "ProductTranslation")

    profiles = (
        ProductProfile.objects
        .exclude(description="", ingredients="")
        .order_by("pk")
    )
    moved = 0

    for profile in profiles:
        translation, _created = ProductTranslation.objects.get_or_create(
            product_id=profile.product_id,
            language_code=FRENCH,
            defaults={"name": ""},
        )
        translation.description = profile.description
        translation.ingredients = profile.ingredients
        translation.save(update_fields=["description", "ingredients"])
        moved += 1

    copied = (
        ProductTranslation.objects
        .filter(language_code=FRENCH)
        .exclude(description="", ingredients="")
        .count()
    )

    if copied != moved:
        raise RuntimeError(
            f"Moved the text of {moved} products to French, "
            f"but {copied} French translations have text."
        )


def move_text_back_to_profile(apps, schema_editor):
    ProductProfile = apps.get_model("products", "ProductProfile")
    ProductTranslation = apps.get_model("products", "ProductTranslation")

    translations = (
        ProductTranslation.objects
        .filter(language_code=FRENCH)
        .exclude(description="", ingredients="")
    )

    for translation in translations:
        ProductProfile.objects.update_or_create(
            product_id=translation.product_id,
            defaults={
                "description": translation.description,
                "ingredients": translation.ingredients,
            },
        )

    ProductTranslation.objects.filter(name="").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0009_catalog_text_per_language"),
    ]

    operations = [
        migrations.RunPython(
            move_text_to_french,
            move_text_back_to_profile,
        ),
    ]
