from __future__ import annotations

from decimal import Decimal

import pytest

from orders.product_demand import (
    get_product_delivered_demand_summary,
)
from products.tests.factories import product_factory


@pytest.mark.django_db
def test_product_delivered_demand_summary_is_empty_without_delivered_orders():
    product = product_factory()

    summary = get_product_delivered_demand_summary(
        product=product,
    )

    assert summary.delivered_order_count == 0
    assert summary.delivered_quantity == 0
    assert (
        summary.average_quantity_per_delivered_order
        == Decimal("0.0")
    )
    assert summary.last_delivered_at is None
