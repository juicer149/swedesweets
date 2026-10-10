"""0015 drops the old weight ordering's quantity and unit, but only when
every line is already in stock units."""

from __future__ import annotations

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from customers.tests.factories import customer_factory
from products.tests.factories import product_factory

BEFORE = [("orders", "0014_order_buyer_language_snapshot")]
AFTER = [("orders", "0015_remove_orderline_quantity_and_unit")]

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def historical_apps():
    executor = MigrationExecutor(connection)
    latest_targets = executor.loader.graph.leaf_nodes()

    executor.migrate(BEFORE)
    apps = executor.loader.project_state(BEFORE).apps

    try:
        yield apps
    finally:
        MigrationExecutor(connection).migrate(latest_targets)


def _migrate(targets):
    MigrationExecutor(connection).migrate(targets)


def _line(apps, *, quantity, unit, quantity_in_units):
    product = product_factory(internal_number=1)
    customer = customer_factory()

    Order = apps.get_model("orders", "Order")
    OrderLine = apps.get_model("orders", "OrderLine")
    CommercialPrice = apps.get_model("pricing", "CommercialPrice")

    order = Order.objects.create(customer_id=customer.pk)
    offer = CommercialPrice.objects.create(
        product_id=product.pk,
        channel="business",
        enabled=True,
    )

    return OrderLine.objects.create(
        order_id=order.pk,
        product_id=product.pk,
        quantity=quantity,
        unit=unit,
        quantity_in_units=quantity_in_units,
        commercial_offer_id=offer.pk,
    )


def test_stock_unit_lines_keep_their_count(historical_apps):
    line = _line(
        historical_apps,
        quantity=4,
        unit="stock_unit",
        quantity_in_units=4,
    )

    _migrate(AFTER)

    with connection.cursor() as cursor:
        columns = {
            column.name
            for column in connection.introspection.get_table_description(
                cursor,
                "orders_orderline",
            )
        }
        cursor.execute(
            "SELECT quantity_in_units FROM orders_orderline WHERE id = %s",
            [line.pk],
        )
        (quantity_in_units,) = cursor.fetchone()

    assert "quantity" not in columns
    assert "unit" not in columns
    assert quantity_in_units == 4


def test_a_weight_line_stops_the_migration(historical_apps):
    line = _line(
        historical_apps,
        quantity="12.5",
        unit="kg",
        quantity_in_units=3,
    )

    with pytest.raises(RuntimeError, match=f"line {line.pk} "):
        _migrate(AFTER)

    # Nothing was dropped: the line is still there as it was.
    line.refresh_from_db()
    assert line.unit == "kg"

    # Let the fixture bring the database back to the latest state.
    line.delete()
