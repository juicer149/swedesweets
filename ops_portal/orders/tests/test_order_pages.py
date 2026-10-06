from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.tests.factories import full_staff_user_factory
from business.services import create_order
from business.tests.factories import standard_business_offer_factory
from customers.tests.factories import customer_factory
from fulfillment.services import pack_order
from inventory.tests.conftest import TODAY
from inventory.tests.factories import batch_factory
from orders.datatypes import OrderLineInput
from products.tests.factories import product_factory


@pytest.fixture
def placed_order():
    product = product_factory(
        name="Apple",
        internal_number=401,
    )
    standard_business_offer_factory(product=product)
    batch_factory(
        product=product,
        today=TODAY,
        quantity=100,
    )

    return create_order(
        customer=customer_factory(email="ops-pages@example.com"),
        lines=[OrderLineInput.units(product=product, quantity=3)],
    )


@pytest.fixture
def staff_client(client):
    client.force_login(full_staff_user_factory())
    return client


def _url(name, order):
    return reverse(name, kwargs={"order_id": order.pk})


def _get(client, name, order):
    response = client.get(_url(name, order))
    assert response.status_code == 200
    return response, response.content.decode()


@pytest.mark.django_db
def test_detail_shows_lines_buyer_dates_and_pack_action(staff_client, placed_order):
    response, content = _get(staff_client, "ops_orders:detail", placed_order)

    (line,) = response.context["content_lines"]
    assert line.quantity == 3
    assert line.image_url is None

    assert f'href="{line.product_detail_href}"' in content
    assert f"mailto:{placed_order.customer_email}" in content
    assert [date.label for date in response.context["dates"]][0] == "Created"
    assert f'href="{_url("ops_orders:pack", placed_order)}"' in content
    assert f'href="{reverse("ops_orders:index")}"' in content


@pytest.mark.django_db
def test_pack_page_keeps_checklist_hooks(staff_client, placed_order):
    _, content = _get(staff_client, "ops_orders:pack", placed_order)

    assert "data-pack-checklist" in content
    assert "data-pack-line-checkbox" in content
    assert 'data-action-behavior="pack-checklist"' in content
    assert f'href="{_url("ops_orders:detail", placed_order)}"' in content


@pytest.mark.django_db
def test_deliver_page_shows_buyer_and_confirm(staff_client, placed_order):
    pack_order(order=placed_order)

    _, content = _get(staff_client, "ops_orders:deliver", placed_order)

    assert "Confirm delivered" in content
    assert f"mailto:{placed_order.customer_email}" in content


@pytest.mark.django_db
def test_cancel_page_shows_form(staff_client, placed_order):
    _, content = _get(staff_client, "ops_orders:cancel", placed_order)

    assert 'name="reason"' in content
    assert 'name="note"' in content
