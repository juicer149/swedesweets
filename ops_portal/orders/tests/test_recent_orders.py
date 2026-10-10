from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.tests.factories import full_staff_user_factory
from business.services import create_order
from business.tests.factories import standard_business_offer_factory
from customers.tests.factories import customer_factory
from inventory.tests.conftest import TODAY
from inventory.tests.factories import batch_factory
from orders.datatypes import OrderLineInput
from orders.models import Order
from products.tests.factories import product_factory


@pytest.fixture
def staff_client(client):
    client.force_login(full_staff_user_factory())
    return client


def _stocked_product(name: str, *, quantity: int = 100):
    product = product_factory(name=name)
    offer = standard_business_offer_factory(product=product)
    batch_factory(
        product=product,
        today=TODAY,
        quantity=quantity,
        batch_id=f"OPS-RO-{name.upper()}",
    )
    return product, offer


def _order(customer, product, quantity: int = 3) -> Order:
    return create_order(
        customer=customer,
        lines=[OrderLineInput.units(product=product, quantity=quantity)],
    )


def _recent_orders_url(customer) -> str:
    return (
        reverse("ops_orders:customer_recent_orders")
        + f"?customer={customer.pk}"
    )


@pytest.mark.django_db
def test_new_order_fetches_the_chosen_customers_last_orders(staff_client):
    customer = customer_factory(email="recent-ops@example.com")
    product, offer = _stocked_product("Apple")
    order = _order(customer, product, quantity=3)

    response = staff_client.get(_recent_orders_url(customer))
    content = response.content.decode()

    assert response.status_code == 200
    assert f"Order #{order.pk}" in content
    # The form's own buttons: they add lines in the page, no posting.
    assert "data-recent-order-repeat" in content
    assert f'data-offer-id="{offer.pk}"' in content
    assert 'data-quantity="3"' in content
    assert "<form" not in content


@pytest.mark.django_db
def test_new_order_page_has_the_place_for_them(staff_client):
    content = staff_client.get(reverse("ops_orders:create")).content.decode()

    assert (
        f'data-recent-orders-url="{reverse("ops_orders:customer_recent_orders")}"'
        in content
    )


@pytest.mark.django_db
@pytest.mark.parametrize("raw", ["", "abc", "0", "999999"])
def test_recent_orders_for_no_such_customer_is_not_found(staff_client, raw):
    response = staff_client.get(
        reverse("ops_orders:customer_recent_orders") + f"?customer={raw}"
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_a_product_that_cannot_be_chosen_now_has_no_plus(staff_client):
    customer = customer_factory(email="recent-ops-gone@example.com")
    product, offer = _stocked_product("Pear", quantity=2)
    # The order takes the last two: nothing left to choose.
    _order(customer, product, quantity=2)

    content = staff_client.get(_recent_orders_url(customer)).content.decode()

    assert f'data-offer-id="{offer.pk}"' not in content
    assert "Not available right now" in content


@pytest.mark.django_db
def test_edit_shows_the_customers_other_orders(staff_client):
    customer = customer_factory(email="recent-ops-edit@example.com")
    product, _offer = _stocked_product("Plum")
    earlier = _order(customer, product)
    current = _order(customer, product)

    response = staff_client.get(
        reverse("ops_orders:edit", kwargs={"order_id": current.pk})
    )
    recent = response.context["recent_orders"]

    assert [order.order_id for order in recent] == [earlier.pk]
