from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("customers", "0003_customer_activated_at_customer_activated_by_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="listed_publicly",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="customer",
            name="store_address_line",
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name="customer",
            name="store_city",
            field=models.CharField(blank=True, max_length=120),
        ),
    ]
