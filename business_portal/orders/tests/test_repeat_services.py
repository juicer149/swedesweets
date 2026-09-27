from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest

from business.models import BusinessOfferSelection
from business.services import (
    add_catalog_offer_to_draft_order,
    create_order,
    place_order,
)
from business.tests.factories import (
    standard_business_offer_factory,
)
from business_portal.orders.repeat_services import (
    RepeatOrderSkipReason,
    repeat_order_into_cart,
)
from customers.tests.factories import customer_factory
from inventory.services import create_batch
from inventory.tests.conftest import TODAY
from inventory.tests.factories import batch_factory
from orders.datatypes import OrderLineInput
from orders.models import Order
from pricing.models import (
    CommercialPrice,
    PriceAmount,
)
from products.tests.factories import product_factory


def _customer(
    *,
    email: str = "repeat@example.com",
):
    return customer_factory(
        email=email,
    )


def _product(
    *,
    name: str,
    internal_number: int,
):
    return product_factory(
        brand="Generic",
        name=name,
        weight_per_unit=5000,
        internal_number=internal_number,
    )


def _stock(
    *,
    product,
    quantity: int = 100,
):
    return batch_factory(
        product=product,
        today=TODAY,
        quantity=quantity,
        batch_id=f"TEST-{product.pk}",
    )


@pytest.mark.django_db
def test_repeat_order_adds_standard_line_to_cart():
    customer = _customer()

    apple = _product(
        name="Apple",
        internal_number=101,
    )

    _stock(
        product=apple,
    )

    standard_offer = (
        standard_business_offer_factory(
            product=apple,
        )
    )

    source_order = create_order(
        customer=customer,
        lines=[
            OrderLineInput.units(
                product=apple,
                quantity=2,
            ),
        ],
    )

    result = repeat_order_into_cart(
        customer=customer,
        source_order=source_order,
    )

    assert result.added_count == 1
    assert result.skipped == ()
    assert result.cart is not None

    line = result.cart.lines.get()

    assert line.commercial_price == standard_offer
    assert line.commercial_price.product == apple
    assert line.quantity == 2

    assert not Order.objects.filter(
        customer=customer,
        channel=Order.Channel.BUSINESS,
        status=Order.Status.DRAFT,
    ).exists()


@pytest.mark.django_db
def test_repeat_order_preserves_selected_special_offer_from_order_line():
    customer = _customer()

    apple = _product(
        name="Apple",
        internal_number=102,
    )

    standard_business_offer_factory(
        product=apple,
    )

    batch = create_batch(
        batch_id="APPLE-SPECIAL",
        product=apple,
        quantity=20,
        best_before=(
            TODAY + timedelta(days=30)
        ),
        location="Shelf A1",
        today=TODAY,
    )

    commercial_price = CommercialPrice.objects.create(
        product=apple,
        batch=batch,
        channel=CommercialPrice.Channel.BUSINESS,
        enabled=True,
        reason=CommercialPrice.Reason.SHORT_DATED,
    )

    PriceAmount.objects.create(
        commercial_price=commercial_price,
        currency=PriceAmount.Currency.EUR,
        price=Decimal("8.50"),
    )

    source_order = add_catalog_offer_to_draft_order(
        customer=customer,
        product=apple,
        commercial_price_id=commercial_price.pk,
        quantity=2,
    )

    source_order = place_order(
        order=source_order,
    )

    source_line = source_order.lines.get()

    assert (
        source_line.commercial_offer_id
        == commercial_price.pk
    )

    BusinessOfferSelection.objects.filter(
        order_line=source_line,
    ).delete()

    result = repeat_order_into_cart(
        customer=customer,
        source_order=source_order,
    )

    assert result.added_count == 1
    assert result.skipped == ()
    assert result.cart is not None

    repeated_line = result.cart.lines.get()

    assert (
        repeated_line.commercial_price_id
        == commercial_price.pk
    )
    assert repeated_line.quantity == 2


@pytest.mark.django_db
def test_repeat_order_skips_inactive_product_without_creating_cart():
    customer = _customer()

    apple = _product(
        name="Apple",
        internal_number=103,
    )

    _stock(
        product=apple,
    )

    standard_business_offer_factory(
        product=apple,
    )

    source_order = create_order(
        customer=customer,
        lines=[
            OrderLineInput.units(
                product=apple,
                quantity=2,
            ),
        ],
    )

    apple.active = False
    apple.save(
        update_fields=[
            "active",
        ]
    )

    result = repeat_order_into_cart(
        customer=customer,
        source_order=source_order,
    )

    assert result.added_count == 0
    assert result.cart is None
    assert len(result.skipped) == 1

    skipped = result.skipped[0]

    assert skipped.product == apple
    assert skipped.quantity == 2
    assert (
        skipped.reason
        == RepeatOrderSkipReason.PRODUCT_UNAVAILABLE
    )


@pytest.mark.django_db
def test_repeat_order_skips_offer_that_is_no_longer_available():
    customer = _customer()

    apple = _product(
        name="Apple",
        internal_number=104,
    )

    _stock(
        product=apple,
    )

    standard_offer = (
        standard_business_offer_factory(
            product=apple,
        )
    )

    source_order = create_order(
        customer=customer,
        lines=[
            OrderLineInput.units(
                product=apple,
                quantity=2,
            ),
        ],
    )

    standard_offer.enabled = False
    standard_offer.save(
        update_fields=[
            "enabled",
        ]
    )

    result = repeat_order_into_cart(
        customer=customer,
        source_order=source_order,
    )

    assert result.added_count == 0
    assert result.cart is None
    assert len(result.skipped) == 1

    skipped = result.skipped[0]

    assert skipped.product == apple
    assert skipped.quantity == 2
    assert (
        skipped.reason
        == RepeatOrderSkipReason.OFFER_UNAVAILABLE
    )


@pytest.mark.django_db
def test_repeat_order_allows_quantity_that_is_not_currently_in_stock():
    customer = _customer()

    apple = _product(
        name="Apple",
        internal_number=105,
    )

    _stock(
        product=apple,
        quantity=4,
    )

    standard_offer = (
        standard_business_offer_factory(
            product=apple,
        )
    )

    source_order = create_order(
        customer=customer,
        lines=[
            OrderLineInput.units(
                product=apple,
                quantity=4,
            ),
        ],
    )

    result = repeat_order_into_cart(
        customer=customer,
        source_order=source_order,
    )

    assert result.added_count == 1
    assert result.skipped == ()
    assert result.cart is not None

    line = result.cart.lines.get()

    assert line.commercial_price == standard_offer
    assert line.quantity == 4


@pytest.mark.django_db
def test_repeat_order_keeps_successful_lines_when_another_line_is_skipped():
    customer = _customer()

    apple = _product(
        name="Apple",
        internal_number=106,
    )

    banana = _product(
        name="Banana",
        internal_number=107,
    )

    _stock(
        product=apple,
    )

    _stock(
        product=banana,
    )

    apple_offer = standard_business_offer_factory(
        product=apple,
    )

    standard_business_offer_factory(
        product=banana,
    )

    source_order = create_order(
        customer=customer,
        lines=[
            OrderLineInput.units(
                product=apple,
                quantity=2,
            ),
            OrderLineInput.units(
                product=banana,
                quantity=3,
            ),
        ],
    )

    banana.active = False
    banana.save(
        update_fields=[
            "active",
        ]
    )

    result = repeat_order_into_cart(
        customer=customer,
        source_order=source_order,
    )

    assert result.added_count == 1
    assert len(result.skipped) == 1
    assert result.cart is not None

    skipped = result.skipped[0]

    assert skipped.product == banana
    assert (
        skipped.reason
        == RepeatOrderSkipReason.PRODUCT_UNAVAILABLE
    )

    assert list(
        result.cart.lines.values_list(
            "commercial_price_id",
            "quantity",
        )
    ) == [
        (
            apple_offer.id,
            2,
        ),
    ]
