from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0004_storelisting'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='phone_number',
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AlterField(
            model_name='customer',
            name='city',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AlterField(
            model_name='customer',
            name='address_line',
            field=models.CharField(blank=True, max_length=180),
        ),
    ]
