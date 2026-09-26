from __future__ import annotations

import pytest

from carts.models import CartLine
from carts.services import (
    InvalidCart,
    add_cart_line,
    clear_cart,
    create_cart,
    remove_cart_line,
    update_cart_line_quantity,
)
from common.channels import SalesChannel
from pricing.models import CommercialPrice
from products.tests.factories import product_factory


def _commercial_price(
    *,
    channel: SalesChannel,
    product=None,
) -> CommercialPrice:
    if product is None:
        product = product_factory()

    return CommercialPrice.objects.create(
        product=product,
        channel=channel,
        enabled=True,
    )


@pytest.mark.django_db
def test_create_cart_preserves_channel():
    cart = create_cart(
        channel=SalesChannel.RETAIL,
    )

    assert cart.channel == SalesChannel.RETAIL


@pytest.mark.django_db
def test_add_cart_line_merges_same_commercial_price():
    cart = create_cart(
        channel=SalesChannel.RETAIL,
    )
    commercial_price = _commercial_price(
        channel=SalesChannel.RETAIL,
    )

    first = add_cart_line(
        cart=cart,
        commercial_price=commercial_price,
        quantity=2,
    )
    second = add_cart_line(
        cart=cart,
        commercial_price=commercial_price,
        quantity=3,
    )

    assert first.pk == second.pk
    assert second.quantity == 5
    assert CartLine.objects.count() == 1


@pytest.mark.django_db
def test_add_cart_line_rejects_other_channel():
    cart = create_cart(
        channel=SalesChannel.RETAIL,
    )
    commercial_price = _commercial_price(
        channel=SalesChannel.BUSINESS,
    )

    with pytest.raises(
        InvalidCart,
        match="commercial price does not belong to cart channel",
    ):
        add_cart_line(
            cart=cart,
            commercial_price=commercial_price,
            quantity=1,
        )

    assert not CartLine.objects.exists()


@pytest.mark.django_db
def test_update_cart_line_quantity():
    cart = create_cart(
        channel=SalesChannel.RETAIL,
    )
    commercial_price = _commercial_price(
        channel=SalesChannel.RETAIL,
    )
    line = add_cart_line(
        cart=cart,
        commercial_price=commercial_price,
        quantity=2,
    )

    line = update_cart_line_quantity(
        cart=cart,
        line=line,
        quantity=7,
    )

    assert line.quantity == 7


@pytest.mark.django_db
def test_cart_line_mutation_rejects_line_from_other_cart():
    first_cart = create_cart(
        channel=SalesChannel.RETAIL,
    )
    second_cart = create_cart(
        channel=SalesChannel.RETAIL,
    )
    commercial_price = _commercial_price(
        channel=SalesChannel.RETAIL,
    )
    line = add_cart_line(
        cart=first_cart,
        commercial_price=commercial_price,
        quantity=1,
    )

    with pytest.raises(
        InvalidCart,
        match="cart line does not belong to cart",
    ):
        update_cart_line_quantity(
            cart=second_cart,
            line=line,
            quantity=2,
        )


@pytest.mark.django_db
def test_remove_cart_line():
    cart = create_cart(
        channel=SalesChannel.RETAIL,
    )
    commercial_price = _commercial_price(
        channel=SalesChannel.RETAIL,
    )
    line = add_cart_line(
        cart=cart,
        commercial_price=commercial_price,
        quantity=1,
    )

    remove_cart_line(
        cart=cart,
        line=line,
    )

    assert not CartLine.objects.filter(
        pk=line.pk,
    ).exists()


@pytest.mark.django_db
def test_clear_cart():
    cart = create_cart(
        channel=SalesChannel.RETAIL,
    )
    commercial_price = _commercial_price(
        channel=SalesChannel.RETAIL,
    )
    add_cart_line(
        cart=cart,
        commercial_price=commercial_price,
        quantity=2,
    )

    clear_cart(
        cart=cart,
    )

    assert cart.lines.count() == 0


@pytest.mark.django_db
def test_create_cart_rejects_invalid_channel():
    with pytest.raises(
        InvalidCart,
        match="invalid sales channel",
    ):
        create_cart(
            channel="invalid",
        )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "quantity",
    [0, -1],
)
def test_add_cart_line_rejects_non_positive_quantity(
    quantity: int,
):
    cart = create_cart(
        channel=SalesChannel.RETAIL,
    )
    commercial_price = _commercial_price(
        channel=SalesChannel.RETAIL,
    )

    with pytest.raises(
        InvalidCart,
        match="cart line quantity must be positive",
    ):
        add_cart_line(
            cart=cart,
            commercial_price=commercial_price,
            quantity=quantity,
        )

    assert not CartLine.objects.exists()
