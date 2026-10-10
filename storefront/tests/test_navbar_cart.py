from __future__ import annotations

from decimal import Decimal

import pytest
from django.http import HttpResponse
from django.urls import reverse

from carts.models import (
    Cart,
    CartLine,
)
from carts.services import create_cart
from common.channels import SalesChannel
from retail.services import add_retail_cart_line
from retail.tests.factories import (
    retail_product_price_factory,
)
from storefront.cart import (
    COOKIE_NAME,
    COOKIE_SALT,
)


def _set_signed_retail_cart_cookie(
    client,
    *,
    cart: Cart,
) -> None:
    response = HttpResponse()

    response.set_signed_cookie(
        COOKIE_NAME,
        str(cart.id),
        salt=COOKIE_SALT,
    )

    client.cookies[COOKIE_NAME] = (
        response.cookies[COOKIE_NAME].value
    )


@pytest.fixture
def retail_price(db):
    return retail_product_price_factory(
        enabled=True,
        price=Decimal("10.00"),
    )


@pytest.mark.django_db
def test_storefront_navbar_cart_does_not_create_cart_on_get(
    client,
):
    assert Cart.objects.count() == 0

    response = client.get(
        reverse("storefront:product_list")
    )

    assert response.status_code == 200
    assert Cart.objects.count() == 0


@pytest.mark.django_db
def test_navbar_cart_fragment_renders_existing_retail_cart(
    client,
    retail_price,
):
    cart = create_cart(
        channel=SalesChannel.RETAIL,
    )

    add_retail_cart_line(
        cart=cart,
        commercial_price_id=retail_price.id,
        quantity=2,
    )

    _set_signed_retail_cart_cookie(
        client,
        cart=cart,
    )

    response = client.get(
        reverse(
            "storefront:navbar_cart_fragment"
        )
    )

    content = response.content.decode()

    assert response.status_code == 200
    assert retail_price.product.display_name in content
    # Read-only: the quantity is shown, not an input.
    assert "× 2" in content
    assert "data-quantity-input" not in content


@pytest.mark.django_db
def test_navbar_cart_quantity_updates_owned_line(
    client,
    retail_price,
):
    cart = create_cart(
        channel=SalesChannel.RETAIL,
    )

    line = add_retail_cart_line(
        cart=cart,
        commercial_price_id=retail_price.id,
        quantity=1,
    )

    _set_signed_retail_cart_cookie(
        client,
        cart=cart,
    )

    response = client.post(
        reverse(
            "storefront:set_cart_line_quantity",
            kwargs={
                "cart_line_id": line.id,
            },
        ),
        {
            "quantity": "3",
        },
        HTTP_ACCEPT="application/json",
    )

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "message": "Quantity updated.",
        "quantity": 3,
        "line_total_label": "€30.00",
        "subtotal_label": "€30.00",
    }

    line.refresh_from_db()

    assert line.quantity == 3


@pytest.mark.django_db
def test_navbar_cart_cannot_update_line_from_other_cart(
    client,
    retail_price,
):
    own_cart = create_cart(
        channel=SalesChannel.RETAIL,
    )
    other_cart = create_cart(
        channel=SalesChannel.RETAIL,
    )

    other_line = add_retail_cart_line(
        cart=other_cart,
        commercial_price_id=retail_price.id,
        quantity=1,
    )

    _set_signed_retail_cart_cookie(
        client,
        cart=own_cart,
    )

    response = client.post(
        reverse(
            "storefront:set_cart_line_quantity",
            kwargs={
                "cart_line_id": other_line.id,
            },
        ),
        {
            "quantity": "3",
        },
        HTTP_ACCEPT="application/json",
    )

    assert response.status_code == 404

    other_line.refresh_from_db()

    assert other_line.quantity == 1


@pytest.mark.django_db
def test_navbar_cart_removes_owned_line(
    client,
    retail_price,
):
    cart = create_cart(
        channel=SalesChannel.RETAIL,
    )

    line = add_retail_cart_line(
        cart=cart,
        commercial_price_id=retail_price.id,
        quantity=1,
    )

    _set_signed_retail_cart_cookie(
        client,
        cart=cart,
    )

    response = client.post(
        reverse(
            "storefront:remove_cart_line",
            kwargs={
                "cart_line_id": line.id,
            },
        ),
        HTTP_ACCEPT="application/json",
    )

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "message": "Product removed from your cart.",
        # The cart is empty now: no subtotal to show.
        "subtotal_label": None,
    }

    assert not CartLine.objects.filter(
        pk=line.id,
    ).exists()
