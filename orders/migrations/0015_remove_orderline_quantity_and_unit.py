"""Order lines count stock units only: drop the old weight ordering's
quantity (kg, grams) and unit.

Before dropping, every line must already be in stock units with the same
count in both fields; otherwise the migration stops and lists the lines,
so nothing is lost without a look.
"""

from django.db import migrations
from django.db.models import F, Q


def check_lines_are_stock_units(apps, schema_editor):
    OrderLine = apps.get_model("orders", "OrderLine")

    offending = list(
        OrderLine.objects.filter(
            ~Q(unit="stock_unit") | ~Q(quantity=F("quantity_in_units"))
        )
        .order_by("pk")
        .values_list("pk", "order_id", "quantity", "unit", "quantity_in_units")[:50]
    )

    if offending:
        rows = "\n".join(
            f"  line {pk} (order {order_id}): "
            f"quantity={quantity} unit={unit} quantity_in_units={units}"
            for pk, order_id, quantity, unit, units in offending
        )
        raise RuntimeError(
            "Some order lines are not in stock units, so their quantity and "
            "unit cannot be dropped safely. Fix these first (at most 50 "
            f"shown):\n{rows}"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0014_order_buyer_language_snapshot"),
    ]

    operations = [
        migrations.RunPython(
            check_lines_are_stock_units,
            migrations.RunPython.noop,
        ),
        migrations.RemoveConstraint(
            model_name="orderline",
            name="orderline_quantity_gt_0",
        ),
        migrations.RemoveField(
            model_name="orderline",
            name="quantity",
        ),
        migrations.RemoveField(
            model_name="orderline",
            name="unit",
        ),
    ]
