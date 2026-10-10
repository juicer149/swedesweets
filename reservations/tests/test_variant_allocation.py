"""An order line's stock comes only from batches of its variant, however
wide the pool (docs/product-variants.md, rule 8)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from inventory.models import InventoryBatch
from inventory.services import create_batch
from orders.models import Order
from orders.tests.factories import order_line_factory
from pricing.models import CommercialPrice
from products.tests.factories import product_factory, variant_factory
from reservations.models import Allocation
from reservations.planning import InsufficientReservationCapacity
from reservations.services import reserve_order_line_from_pool

TODAY = timezone.localdate()


@pytest.fixture
def hoodie():
    product = product_factory(name="Hoodie")
    medium = variant_factory(product=product, label="M")
    large = variant_factory(product=product, label="L")

    # Large has more stock, and sooner best-before: FEFO would take it.
    create_batch(
        batch_id="H-L-1",
        product=product,
        variant=large,
        quantity=10,
        best_before=TODAY + timedelta(days=30),
        location="Shelf A1",
        today=TODAY,
    )
    create_batch(
        batch_id="H-M-1",
        product=product,
        variant=medium,
        quantity=2,
        best_before=TODAY + timedelta(days=60),
        location="Shelf A2",
        today=TODAY,
    )

    return product, medium


def _medium_line(*, product, medium, quantity):
    offer = CommercialPrice.objects.create(
        variant=medium,
        channel=CommercialPrice.Channel.RETAIL,
        enabled=True,
    )
    order = Order.objects.create(
        channel=Order.Channel.RETAIL,
        customer=None,
    )

    return order_line_factory(
        order=order,
        product=product,
        commercial_offer=offer,
        quantity=quantity,
    )


@pytest.mark.django_db
def test_a_line_takes_stock_only_from_its_variant(hoodie):
    product, medium = hoodie
    line = _medium_line(product=product, medium=medium, quantity=2)

    assert line.variant == medium

    reserve_order_line_from_pool(
        order_line=line,
        batches=InventoryBatch.objects.filter(product=product),
        quantity=2,
    )

    assert [
        (allocation.batch.batch_id, allocation.quantity)
        for allocation in Allocation.objects.filter(order_line=line)
    ] == [("H-M-1", 2)]


@pytest.mark.django_db
def test_another_variant_stock_does_not_make_up_a_shortfall(hoodie):
    product, medium = hoodie
    line = _medium_line(product=product, medium=medium, quantity=3)

    with pytest.raises(InsufficientReservationCapacity):
        reserve_order_line_from_pool(
            order_line=line,
            batches=InventoryBatch.objects.filter(product=product),
            quantity=3,
        )
