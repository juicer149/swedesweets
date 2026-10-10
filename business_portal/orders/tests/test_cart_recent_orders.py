from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.tests.factories import (
    customer_user_factory,
)
from business.models import BusinessCart
from business.services import create_order
from business.tests.factories import (
    standard_business_offer_factory,
)
from customers.tests.factories import (
    customer_factory,
)
from inventory.tests.conftest import TODAY
from inventory.tests.factories import (
    batch_factory,
)
from orders.datatypes import OrderLineInput
from orders.models import Order
from products.tests.factories import (
    product_factory,
)


def _login_customer(
    *,
    client,
):
    customer = customer_factory()

    client.force_login(
        customer_user_factory(
            customer=customer,
        )
    )

    return customer


def _stocked_product(
    *,
    name: str,
    quantity: int = 100,
):
    product = product_factory(
        name=name,
        weight_per_unit=2000,
    )
    offer = standard_business_offer_factory(
        product=product,
    )
    batch_factory(
        product=product,
        today=TODAY,
        quantity=quantity,
        batch_id=f"RO-{name.upper()}",
    )

    return product, offer


def _order(
    *,
    customer,
    product,
    quantity: int = 2,
) -> Order:
    return create_order(
        customer=customer,
        lines=[
            OrderLineInput.units(
                product=product,
                quantity=quantity,
            ),
        ],
    )


@pytest.mark.django_db
def test_cart_shows_the_last_three_orders_newest_first(
    client,
):
    customer = _login_customer(
        client=client,
    )
    product, offer = _stocked_product(
        name="Apple",
    )
    orders = [
        _order(customer=customer, product=product)
        for _ in range(4)
    ]
    cancelled = _order(
        customer=customer,
        product=product,
    )
    Order.objects.filter(pk=cancelled.pk).update(
        status=Order.Status.CANCELLED,
    )

    response = client.get(
        reverse("business_portal:cart")
    )
    recent = response.context["recent_orders"]

    assert [order.order_id for order in recent] == [
        order.pk for order in reversed(orders[1:])
    ]
    assert recent[0].lines[0].quantity == 2
    # Still in the catalog: its "+" adds that offer.
    assert recent[0].lines[0].commercial_price_id == offer.pk
    assert "data-cart-repeat" in response.content.decode()
    assert "data-cart-add-offer" in response.content.decode()


@pytest.mark.django_db
def test_a_product_out_of_the_catalog_has_no_plus(
    client,
):
    customer = _login_customer(
        client=client,
    )
    product, _offer = _stocked_product(
        name="Apple",
        quantity=2,
    )
    # The order takes the last two: nothing left to order now.
    _order(
        customer=customer,
        product=product,
        quantity=2,
    )

    response = client.get(
        reverse("business_portal:cart")
    )

    line = response.context["recent_orders"][0].lines[0]

    assert line.commercial_price_id is None


@pytest.mark.django_db
def test_no_previous_orders_no_section(
    client,
):
    _login_customer(
        client=client,
    )

    response = client.get(
        reverse("business_portal:cart")
    )

    assert response.context["recent_orders"] == ()
    assert "recent-orders" not in response.content.decode()


@pytest.mark.django_db
def test_order_again_answers_a_script_with_the_lines_drawn(
    client,
):
    customer = _login_customer(
        client=client,
    )
    product, offer = _stocked_product(
        name="Apple",
    )
    order = _order(
        customer=customer,
        product=product,
        quantity=3,
    )

    response = client.post(
        reverse(
            "business_portal:repeat_order",
            kwargs={"order_id": order.pk},
        ),
        HTTP_ACCEPT="application/json",
    )
    payload = response.json()
    cart_line = BusinessCart.objects.get(
        customer=customer,
    ).cart.lines.get()

    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["notes"] == []
    assert [line["cart_line_id"] for line in payload["lines"]] == [
        cart_line.pk
    ]
    assert payload["lines"][0]["quantity"] == 3
    assert (
        f'data-cart-line-id="{cart_line.pk}"'
        in payload["lines"][0]["line_html"]
    )
    assert cart_line.commercial_price_id == offer.pk
