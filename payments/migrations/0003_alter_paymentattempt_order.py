from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0002_paymentattempt_provider_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="paymentattempt",
            name="order",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="payment_attempts",
                to="orders.order",
            ),
        ),
    ]
