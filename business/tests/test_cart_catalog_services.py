from __future__ import annotations

from decimal import Decimal

import pytest

from business.cart_services import (
    InvalidBusinessCart,
    add_catalog_offer_to_cart,
)
from business.models import BusinessCart
from business.tests.factories import (
    standard_business_offer_factory,
)
from carts.models import CartLine
from common.channels import SalesChannel
from orders.models import Order
from orders.order_limits import (
    MAX_QUANTITY_PER_PRODUCT_PER_ORDER,
)
from pricing.models import CommercialPrice
from pricing.tests.factories import (
    commercial_price_factory,
    price_amount_factory,
    pricing_batch_factory,
)
from products.tests.factories import product_factory


@pytest.mark.django_db
def test_add_standard_business_offer_to_cart(
    customer,
    apple,
):
    offer = standard_business_offer_factory(
        product=apple,
    )

    line = add_catalog_offer_to_cart(
        customer=customer,
        product=apple,
        commercial_price_id=offer.pk,
        quantity=2,
    )

    assert line.cart.channel == SalesChannel.BUSINESS
    assert line.commercial_price == offer
    assert line.quantity == 2
    assert line.cart.business_context.customer == customer

    assert not Order.objects.filter(
        customer=customer,
        status=Order.Status.DRAFT,
    ).exists()


@pytest.mark.django_db
def test_missing_offer_id_selects_standard_business_offer(
    customer,
    apple,
):
    offer = standard_business_offer_factory(
        product=apple,
    )

    line = add_catalog_offer_to_cart(
        customer=customer,
        product=apple,
        commercial_price_id=None,
    )

    assert line.commercial_price == offer
    assert line.quantity == 1


@pytest.mark.django_db
def test_add_batch_business_offer_to_cart(
    customer,
    apple,
):
    standard_business_offer_factory(
        product=apple,
    )

    batch = pricing_batch_factory(
        product=apple,
        batch_id="BUS-CART-001",
    )

    offer = commercial_price_factory(
        product=apple,
        batch=batch,
        channel=CommercialPrice.Channel.BUSINESS,
        enabled=True,
    )

    price_amount_factory(
        commercial_price=offer,
        price=Decimal("8.50"),
    )

    line = add_catalog_offer_to_cart(
        customer=customer,
        product=apple,
        commercial_price_id=offer.pk,
        quantity=3,
    )

    assert line.commercial_price == offer
    assert line.quantity == 3


@pytest.mark.django_db
def test_adding_same_offer_merges_cart_line(
    customer,
    apple,
):
    offer = standard_business_offer_factory(
        product=apple,
    )

    first = add_catalog_offer_to_cart(
        customer=customer,
        product=apple,
        commercial_price_id=offer.pk,
        quantity=2,
    )

    second = add_catalog_offer_to_cart(
        customer=customer,
        product=apple,
        commercial_price_id=offer.pk,
        quantity=3,
    )

    assert second.pk == first.pk
    assert second.quantity == 5
    assert CartLine.objects.count() == 1


@pytest.mark.django_db
def test_different_offers_for_same_product_remain_separate(
    customer,
    apple,
):
    standard_offer = standard_business_offer_factory(
        product=apple,
    )

    batch = pricing_batch_factory(
        product=apple,
        batch_id="BUS-CART-002",
    )

    batch_offer = commercial_price_factory(
        product=apple,
        batch=batch,
        channel=CommercialPrice.Channel.BUSINESS,
        enabled=True,
    )

    price_amount_factory(
        commercial_price=batch_offer,
        price=Decimal("7.50"),
    )

    first = add_catalog_offer_to_cart(
        customer=customer,
        product=apple,
        commercial_price_id=standard_offer.pk,
        quantity=2,
    )

    second = add_catalog_offer_to_cart(
        customer=customer,
        product=apple,
        commercial_price_id=batch_offer.pk,
        quantity=3,
    )

    assert first.cart_id == second.cart_id

    assert set(
        first.cart.lines.values_list(
            "commercial_price_id",
            "quantity",
        )
    ) == {
        (
            standard_offer.pk,
            2,
        ),
        (
            batch_offer.pk,
            3,
        ),
    }


@pytest.mark.django_db
def test_business_cart_rejects_unknown_offer(
    customer,
    apple,
):
    with pytest.raises(
        InvalidBusinessCart,
        match="business offer is not currently available",
    ):
        add_catalog_offer_to_cart(
            customer=customer,
            product=apple,
            commercial_price_id=999_999,
        )

    assert not BusinessCart.objects.filter(
        customer=customer,
    ).exists()


@pytest.mark.django_db
def test_business_cart_rejects_retail_offer(
    customer,
    apple,
):
    offer = commercial_price_factory(
        product=apple,
        channel=CommercialPrice.Channel.RETAIL,
        enabled=True,
    )

    with pytest.raises(
        InvalidBusinessCart,
        match="business offer is not currently available",
    ):
        add_catalog_offer_to_cart(
            customer=customer,
            product=apple,
            commercial_price_id=offer.pk,
        )

    assert not BusinessCart.objects.filter(
        customer=customer,
    ).exists()


@pytest.mark.django_db
def test_business_cart_rejects_disabled_business_offer(
    customer,
    apple,
):
    offer = commercial_price_factory(
        product=apple,
        channel=CommercialPrice.Channel.BUSINESS,
        enabled=False,
    )

    with pytest.raises(
        InvalidBusinessCart,
        match="business offer is not currently available",
    ):
        add_catalog_offer_to_cart(
            customer=customer,
            product=apple,
            commercial_price_id=offer.pk,
        )

    assert not BusinessCart.objects.filter(
        customer=customer,
    ).exists()


@pytest.mark.django_db
def test_business_cart_rejects_inactive_product_without_standard_offer(
    customer,
    apple,
):
    apple.active = False
    apple.save(
        update_fields=[
            "active",
            "updated_at",
        ],
    )

    with pytest.raises(
        InvalidBusinessCart,
        match="business offer is not currently available",
    ):
        add_catalog_offer_to_cart(
            customer=customer,
            product=apple,
            commercial_price_id=None,
        )

    assert not BusinessCart.objects.filter(
        customer=customer,
    ).exists()


@pytest.mark.django_db
def test_business_cart_rejects_offer_for_other_product(
    customer,
    apple,
):
    other_product = product_factory(
        name="Banana",
    )

    offer = standard_business_offer_factory(
        product=other_product,
    )

    with pytest.raises(
        InvalidBusinessCart,
        match="business offer is not currently available",
    ):
        add_catalog_offer_to_cart(
            customer=customer,
            product=apple,
            commercial_price_id=offer.pk,
        )

    assert not BusinessCart.objects.filter(
        customer=customer,
    ).exists()


@pytest.mark.django_db
def test_business_cart_rejects_batch_offer_without_eur_price(
    customer,
    apple,
):
    batch = pricing_batch_factory(
        product=apple,
        batch_id="BUS-CART-003",
    )

    offer = commercial_price_factory(
        product=apple,
        batch=batch,
        channel=CommercialPrice.Channel.BUSINESS,
        enabled=True,
    )

    with pytest.raises(
        InvalidBusinessCart,
        match="business offer is not currently available",
    ):
        add_catalog_offer_to_cart(
            customer=customer,
            product=apple,
            commercial_price_id=offer.pk,
        )

    assert not BusinessCart.objects.filter(
        customer=customer,
    ).exists()


@pytest.mark.django_db
def test_business_cart_does_not_apply_stock_or_order_quantity_limits(
    customer,
    apple,
):
    offer = standard_business_offer_factory(
        product=apple,
    )

    quantity = (
        MAX_QUANTITY_PER_PRODUCT_PER_ORDER
        + 1
    )

    line = add_catalog_offer_to_cart(
        customer=customer,
        product=apple,
        commercial_price_id=offer.pk,
        quantity=quantity,
    )

    assert line.quantity == quantity


@pytest.mark.django_db
def test_invalid_quantity_does_not_leave_empty_business_cart(
    customer,
    apple,
):
    offer = standard_business_offer_factory(
        product=apple,
    )

    with pytest.raises(
        InvalidBusinessCart,
        match="cart line quantity must be positive",
    ):
        add_catalog_offer_to_cart(
            customer=customer,
            product=apple,
            commercial_price_id=offer.pk,
            quantity=0,
        )

    assert not BusinessCart.objects.filter(
        customer=customer,
    ).exists()
