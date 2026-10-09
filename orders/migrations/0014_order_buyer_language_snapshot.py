from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0013_remove_order_unique_business_draft_order_per_customer'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='buyer_language_snapshot',
            field=models.CharField(blank=True, max_length=10),
        ),
    ]
