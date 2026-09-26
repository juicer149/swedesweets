from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest

from business.cart_services import (
    add_catalog_offer_to_cart,
)
from business.models import BusinessCart
from business.services import (
    place_customer_cart,
)
from business.tests.conftest import TODAY
from business.tests.factories import (
    standard_business_offer_factory,
)
from inventory.errors import (
    InsufficientStockError,
)
from inventory.services import (
    create_batch,
)
from orders.errors import (
    InvalidOrderOperation,
)
from orders.models import Order
from orders.order_limits import (
    MAX_QUANTITY_PER_PRODUCT_PER_ORDER,
)
from pricing.models import (
    CommercialPrice,
    PriceAmount,
)
from reservations.models import Allocation


def _create_stock(
    *,
    product,
    quantity: int,
    batch_id: str = "CART-STOCK-001",
):
    return create_batch(
        batch_id=batch_id,
        product=product,
        quantity=quantity,
        best_before=(
            TODAY + timedelta(days=60)
        ),
        location="Shelf A1",
        today=TODAY,
    )


def _add_eur_price(
    *,
    offer: CommercialPrice,
    price: str,
) -> PriceAmount:
    return PriceAmount.objects.create(
        commercial_price=offer,
        currency=PriceAmount.Currency.EUR,
        price=Decimal(price),
    )


def _create_batch_offer(
    *,
    product,
    quantity: int = 10,
    price: str = "8.50",
) -> CommercialPrice:
    batch = _create_stock(
        product=product,
        quantity=quantity,
        batch_id="CART-SPECIAL-001",
    )

    offer = CommercialPrice.objects.create(
        product=product,
        batch=batch,
        channel=CommercialPrice.Channel.BUSINESS,
        enabled=True,
        reason=CommercialPrice.Reason.PROMOTION,
    )

    _add_eur_price(
        offer=offer,
        price=price,
    )

    return offer


@pytest.mark.django_db
def test_place_customer_cart_creates_placed_order_and_clears_cart(
    customer,
    apple,
):
    stock_batch = _create_stock(
        product=apple,
        quantity=10,
    )

    offer = standard_business_offer_factory(
        product=apple,
    )

    _add_eur_price(
        offer=offer,
        price="9.50",
    )

    cart_line = add_catalog_offer_to_cart(
        customer=customer,
        product=apple,
        commercial_price_id=offer.pk,
        quantity=3,
    )

    business_cart = BusinessCart.objects.get(
        customer=customer,
    )

    cart = business_cart.cart

    placed = place_customer_cart(
        customer=customer,
    )

    assert placed.channel == Order.Channel.BUSINESS
    assert placed.status == Order.Status.PLACED
    assert placed.customer == customer
    assert placed.placed_at is not None

    order_line = placed.lines.get()

    assert order_line.product == apple
    assert order_line.quantity_in_units == 3
    assert (
        order_line.commercial_offer_id
        == cart_line.commercial_price_id
    )
    assert (
        order_line.unit_price_snapshot
        == Decimal("9.50")
    )

    allocation = placed.allocations.get()

    assert allocation.batch == stock_batch
    assert allocation.quantity == 3
    assert (
        allocation.status
        == Allocation.Status.RESERVED
    )
    assert allocation.reserved_until is None

    assert BusinessCart.objects.filter(
        customer=customer,
        cart=cart,
    ).exists()

    assert not cart.lines.exists()


@pytest.mark.django_db
def test_place_customer_cart_rolls_back_when_stock_is_insufficient(
    customer,
    apple,
):
    _create_stock(
        product=apple,
        quantity=2,
    )

    offer = standard_business_offer_factory(
        product=apple,
    )

    cart_line = add_catalog_offer_to_cart(
        customer=customer,
        product=apple,
        commercial_price_id=offer.pk,
        quantity=3,
    )

    order_ids_before = set(
        Order.objects.values_list(
            "id",
            flat=True,
        )
    )

    with pytest.raises(
        InsufficientStockError,
    ) as error:
        place_customer_cart(
            customer=customer,
        )

    assert error.value.requested_quantity == 3
    assert error.value.available_quantity == 2
    assert error.value.missing_quantity == 1

    assert set(
        Order.objects.values_list(
            "id",
            flat=True,
        )
    ) == order_ids_before

    assert not Allocation.objects.exists()

    cart_line.refresh_from_db()

    assert cart_line.quantity == 3
    assert (
        cart_line.commercial_price_id
        == offer.pk
    )


@pytest.mark.django_db
def test_place_customer_cart_rolls_back_when_offer_becomes_unavailable(
    customer,
    apple,
):
    _create_stock(
        product=apple,
        quantity=10,
    )

    offer = standard_business_offer_factory(
        product=apple,
    )

    cart_line = add_catalog_offer_to_cart(
        customer=customer,
        product=apple,
        commercial_price_id=offer.pk,
        quantity=3,
    )

    offer.enabled = False
    offer.save(
        update_fields=[
            "enabled",
        ]
    )

    order_ids_before = set(
        Order.objects.values_list(
            "id",
            flat=True,
        )
    )

    with pytest.raises(
        InvalidOrderOperation,
        match=(
            "selected business offer "
            "is not currently available"
        ),
    ):
        place_customer_cart(
            customer=customer,
        )

    assert set(
        Order.objects.values_list(
            "id",
            flat=True,
        )
    ) == order_ids_before

    assert not Allocation.objects.exists()

    cart_line.refresh_from_db()

    assert cart_line.quantity == 3
    assert (
        cart_line.commercial_price_id
        == offer.pk
    )


@pytest.mark.django_db
def test_place_customer_cart_applies_product_limit_across_distinct_offers(
    customer,
    apple,
):
    standard_offer = (
        standard_business_offer_factory(
            product=apple,
        )
    )

    batch_offer = _create_batch_offer(
        product=apple,
    )

    standard_line = add_catalog_offer_to_cart(
        customer=customer,
        product=apple,
        commercial_price_id=(
            standard_offer.pk
        ),
        quantity=(
            MAX_QUANTITY_PER_PRODUCT_PER_ORDER
        ),
    )

    batch_line = add_catalog_offer_to_cart(
        customer=customer,
        product=apple,
        commercial_price_id=(
            batch_offer.pk
        ),
        quantity=1,
    )

    order_ids_before = set(
        Order.objects.values_list(
            "id",
            flat=True,
        )
    )

    with pytest.raises(
        InvalidOrderOperation,
        match=(
            "maximum quantity per product is "
            f"{MAX_QUANTITY_PER_PRODUCT_PER_ORDER}"
        ),
    ):
        place_customer_cart(
            customer=customer,
        )

    assert set(
        Order.objects.values_list(
            "id",
            flat=True,
        )
    ) == order_ids_before

    assert not Allocation.objects.exists()

    standard_line.refresh_from_db()
    batch_line.refresh_from_db()

    assert (
        standard_line.quantity
        == MAX_QUANTITY_PER_PRODUCT_PER_ORDER
    )
    assert batch_line.quantity == 1
