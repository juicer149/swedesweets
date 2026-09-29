from django.db import migrations


def remove_incorrect_sallanches_postal_area(apps, schema_editor):
    """Remove a seed row with the wrong postal code.

    Sallanches is 74700. The original hardcoded seed listed it under 74300,
    which belongs to Cluses and neighbouring communes.
    """

    RetailPostalArea = apps.get_model("retail", "RetailPostalArea")

    RetailPostalArea.objects.filter(
        country_code="FR",
        postal_code="74300",
        city="Sallanches",
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("retail", "0013_retailcheckoutsession_cart"),
    ]

    operations = [
        migrations.RunPython(
            remove_incorrect_sallanches_postal_area,
            migrations.RunPython.noop,
        ),
    ]
