from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("carts", "0001_initial"),
        ("retail", "0012_delete_retailofferselection"),
    ]

    operations = [
        migrations.AddField(
            model_name="retailcheckoutsession",
            name="cart",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="carts.cart",
            ),
        ),
    ]
