from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0006_remove_productprofile_image_url_productprofile_image_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="productprofile",
            name="display",
            field=models.ImageField(
                blank=True,
                editable=False,
                max_length=255,
                upload_to="products/display/%Y/%m/%d/",
            ),
        ),
    ]
