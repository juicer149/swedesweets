from __future__ import annotations

import pytest

from business.services import create_order
from business.tests.factories import standard_business_offer_factory
from customers.tests.factories import customer_factory
from inventory.services import create_batch
from inventory.tests.conftest import STOCK_EARLY_BEST_BEFORE, TODAY
from orders.datatypes import OrderLineInput
from orders.errors import InvalidOrderOperation
from orders.models import Order
from orders.tests.factories import order_line_factory
from pricing.models import CommercialPrice
from products.tests.factories import product_factory, variant_factory


@pytest.mark.django_db
def test_a_placed_line_is_for_its_offer_variant():
    product = product_factory(name="Apple", internal_number=1)
    standard_business_offer_factory(product=product)
    create_batch(
        batch_id="A-1",
        product=product,
        quantity=10,
        best_before=STOCK_EARLY_BEST_BEFORE,
        location="Shelf A1",
        today=TODAY,
    )

    order = create_order(
        customer=customer_factory(),
        lines=[OrderLineInput.units(product=product, quantity=2)],
    )
    line = order.lines.get()

    assert line.variant == product.variants.get()
    assert line.variant == line.commercial_offer.variant


@pytest.mark.django_db
def test_a_line_cannot_be_for_another_variant_than_its_offer():
    product = product_factory(name="Hoodie")
    medium = variant_factory(product=product, label="M")
    offer = CommercialPrice.objects.create(
        variant=medium,
        channel=CommercialPrice.Channel.RETAIL,
    )
    order = Order.objects.create(channel=Order.Channel.RETAIL)
    line = order_line_factory(
        order=order,
        product=product,
        commercial_offer=offer,
    )

    line.variant = product.variants.get(label="")

    with pytest.raises(InvalidOrderOperation, match="offer's"):
        line.save()
