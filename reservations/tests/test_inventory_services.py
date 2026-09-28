from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from inventory.errors import InvalidStockOperation
from inventory.services import create_batch
from orders.models import Order
from orders.tests.factories import order_line_factory
from reservations.inventory_services import (
    close_batch,
    update_batch,
)
from reservations.models import Allocation


@pytest.mark.django_db
def test_update_batch_rejects_quantity_below_active_reservation(
    product,
):
    today = timezone.localdate()

    batch = create_batch(
        batch_id="A-001",
        product=product,
        quantity=10,
        best_before=today + timedelta(days=60),
        location="Shelf A1",
        today=today,
    )

    order = Order.objects.create(
        channel=Order.Channel.RETAIL,
        customer=None,
    )
    line = order_line_factory(
        order=order,
        product=product,
        quantity=4,
    )

    Allocation.objects.create(
        order=order,
        order_line=line,
        batch=batch,
        quantity=4,
    )

    with pytest.raises(
        InvalidStockOperation,
        match="4 units are reserved",
    ):
        update_batch(
            batch=batch,
            quantity=3,
            best_before=batch.best_before,
            location=batch.location,
        )


@pytest.mark.django_db
def test_close_batch_rejects_active_reservation(
    product,
):
    today = timezone.localdate()

    batch = create_batch(
        batch_id="A-001",
        product=product,
        quantity=10,
        best_before=today + timedelta(days=60),
        location="Shelf A1",
        today=today,
    )

    order = Order.objects.create(
        channel=Order.Channel.RETAIL,
        customer=None,
    )
    line = order_line_factory(
        order=order,
        product=product,
        quantity=4,
    )

    Allocation.objects.create(
        order=order,
        order_line=line,
        batch=batch,
        quantity=4,
    )

    with pytest.raises(
        InvalidStockOperation,
        match="4 units are reserved",
    ):
        close_batch(
            batch=batch,
        )
