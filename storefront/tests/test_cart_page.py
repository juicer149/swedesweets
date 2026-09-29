from __future__ import annotations

from decimal import Decimal

import pytest
from django.http import HttpResponse
from django.urls import reverse

from carts.models import Cart, CartLine
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


@pytest.fixture
def cart_with_line(client, retail_price):
    cart = create_cart(
        channel=SalesChannel.RETAIL,
    )

    line = add_retail_cart_line(
        cart=cart,
        commercial_price_id=retail_price.id,
        quantity=2,
    )

    _set_signed_retail_cart_cookie(
        client,
        cart=cart,
    )

    return cart, line


@pytest.mark.django_db
def test_cart_page_is_reachable_without_a_cart(client):
    response = client.get(
        reverse("storefront:cart")
    )

    assert response.status_code == 200
    assert "Your cart is empty." in response.content.decode()
    assert Cart.objects.count() == 0


@pytest.mark.django_db
def test_cart_page_shows_lines_and_subtotal(
    client,
    retail_price,
    cart_with_line,
):
    response = client.get(
        reverse("storefront:cart")
    )

    content = response.content.decode()

    assert response.status_code == 200
    assert retail_price.product.display_name in content
    assert 'value="2"' in content
    assert "€20.00" in content


@pytest.mark.django_db
def test_quantity_update_returns_new_totals_as_json(
    client,
    cart_with_line,
):
    _cart, line = cart_with_line

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

    payload = response.json()

    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["quantity"] == 3
    assert payload["line_total_label"] == "€30.00"
    assert payload["subtotal_label"] == "€30.00"


@pytest.mark.django_db
def test_remove_without_js_redirects_back_to_cart(
    client,
    cart_with_line,
):
    _cart, line = cart_with_line

    response = client.post(
        reverse(
            "storefront:remove_cart_line",
            kwargs={
                "cart_line_id": line.id,
            },
        )
    )

    assert response.status_code == 302
    assert response.url == reverse("storefront:cart")
    assert not CartLine.objects.filter(pk=line.id).exists()


@pytest.mark.django_db
def test_clear_cart_removes_all_lines(
    client,
    cart_with_line,
):
    cart, _line = cart_with_line

    response = client.post(
        reverse("storefront:cart"),
        {
            "intent": "clear_cart",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("storefront:cart")
    assert not cart.lines.exists()


@pytest.mark.django_db
def test_navbar_cart_links_to_cart_page(
    client,
    cart_with_line,
):
    response = client.get(
        reverse("storefront:navbar_cart_fragment")
    )

    assert reverse("storefront:cart") in response.content.decode()
