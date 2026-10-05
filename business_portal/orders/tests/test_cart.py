from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.tests.factories import (
    customer_user_factory,
)
from business.cart_services import (
    add_catalog_offer_to_cart,
)
from business.models import BusinessCart
from business.tests.factories import (
    standard_business_offer_factory,
)
from carts.models import CartLine
from customers.tests.factories import (
    customer_factory,
)
from products.tests.factories import (
    product_factory,
)


def _login_customer(
    *,
    client,
):
    customer = customer_factory()

    user = customer_user_factory(
        customer=customer,
    )

    client.force_login(
        user
    )

    return customer


def _create_cart_line(
    *,
    customer,
    quantity: int = 3,
):
    product = product_factory(
        name="Apple",
        weight_per_unit=5000,
    )

    offer = standard_business_offer_factory(
        product=product,
    )

    return add_catalog_offer_to_cart(
        customer=customer,
        product=product,
        commercial_price_id=offer.pk,
        quantity=quantity,
    )


@pytest.mark.django_db
def test_cart_does_not_create_empty_cart(
    client,
):
    customer = _login_customer(
        client=client,
    )

    response = client.get(
        reverse(
            "business_portal:cart"
        )
    )

    assert response.status_code == 200
    assert response.context["cart_lines"] == ()

    assert not BusinessCart.objects.filter(
        customer=customer,
    ).exists()


@pytest.mark.django_db
def test_cart_reads_customer_cart(
    client,
):
    customer = _login_customer(
        client=client,
    )

    line = _create_cart_line(
        customer=customer,
        quantity=3,
    )

    response = client.get(
        reverse(
            "business_portal:cart"
        )
    )

    assert response.status_code == 200

    cart_lines = response.context[
        "cart_lines"
    ]

    assert len(cart_lines) == 1

    presented_line = cart_lines[0]

    assert presented_line.cart_line_id == line.id
    assert presented_line.quantity == 3

    assert presented_line.quantity_url == reverse(
        "business_portal:set_cart_line_quantity",
        kwargs={
            "cart_line_id": line.id,
        },
    )

    assert presented_line.remove_url == reverse(
        "business_portal:remove_cart_line",
        kwargs={
            "cart_line_id": line.id,
        },
    )

    product_url = reverse(
        "business_portal:catalog_product",
        kwargs={
            "product_id": line.commercial_price.product_id,
        },
    )

    assert presented_line.product_url == product_url
    assert presented_line.image_url is None
    assert f'href="{product_url}"' in response.content.decode()


@pytest.mark.django_db
def test_cart_does_not_show_another_customers_cart(
    client,
):
    customer = _login_customer(
        client=client,
    )

    other_customer = customer_factory(
        name="Other Customer",
        email="other@example.com",
    )

    _create_cart_line(
        customer=other_customer,
    )

    response = client.get(
        reverse(
            "business_portal:cart"
        )
    )

    assert response.status_code == 200
    assert response.context["cart_lines"] == ()

    assert not BusinessCart.objects.filter(
        customer=customer,
    ).exists()


@pytest.mark.django_db
def test_cart_line_urls_mutate_cart_line(
    client,
):
    customer = _login_customer(
        client=client,
    )

    line = _create_cart_line(
        customer=customer,
        quantity=3,
    )

    response = client.get(
        reverse(
            "business_portal:cart"
        )
    )

    presented_line = response.context[
        "cart_lines"
    ][0]

    response = client.post(
        presented_line.quantity_url,
        {
            "quantity": "5",
        },
    )

    assert response.status_code == 302

    line.refresh_from_db()

    assert line.quantity == 5

    response = client.post(
        presented_line.remove_url,
    )

    assert response.status_code == 302
    assert not CartLine.objects.filter(
        pk=line.pk,
    ).exists()
