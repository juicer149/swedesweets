"""0018 gives the order lines there are their copy of what was bought, from
their variant and product as they are."""

from __future__ import annotations

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from customers.tests.factories import customer_factory
from pricing.models import CommercialPrice
from products.tests.factories import product_factory, variant_factory

BEFORE = [("orders", "0017_alter_orderline_variant")]
AFTER = [("orders", "0018_orderline_snapshot")]

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


def test_existing_lines_get_their_copy(historical_apps):
    product = product_factory(brand="SwedeSweets", name="Hoodie")
    medium = variant_factory(product=product, label="M", weight_per_unit=450)
    # The live model: pricing stays migrated.
    offer = CommercialPrice.objects.create(
        variant=medium,
        channel=CommercialPrice.Channel.BUSINESS,
        enabled=True,
    )
    customer = customer_factory()

    Order = historical_apps.get_model("orders", "Order")
    OrderLine = historical_apps.get_model("orders", "OrderLine")
    order = Order.objects.create(customer_id=customer.pk)
    line = OrderLine.objects.create(
        order_id=order.pk,
        product_id=product.pk,
        variant_id=medium.pk,
        quantity_in_units=2,
        commercial_offer_id=offer.pk,
    )

    MigrationExecutor(connection).migrate(AFTER)
    apps = MigrationExecutor(connection).loader.project_state(AFTER).apps
    line = apps.get_model("orders", "OrderLine").objects.get(pk=line.pk)

    assert line.name_snapshot == "SwedeSweets — Hoodie — M"
    assert line.sku_snapshot == medium.sku
    assert line.variant_label_snapshot == "M"
    assert line.weight_per_unit_snapshot == 450
    assert line.stock_unit_snapshot == product.stock_unit
