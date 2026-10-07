import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("customers", "0003_customer_activated_at_customer_activated_by_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="StoreListing",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("is_listed", models.BooleanField(default=False)),
                ("address_line", models.CharField(blank=True, max_length=180)),
                ("city", models.CharField(blank=True, max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "customer",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="store_listing",
                        to="customers.customer",
                    ),
                ),
            ],
        ),
    ]
