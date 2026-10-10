from __future__ import annotations

from decimal import Decimal

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
from customers.tests.factories import (
    customer_factory,
)
from inventory.tests.conftest import TODAY
from inventory.tests.factories import (
    batch_factory,
)
from pricing.models import CommercialPrice
from pricing.tests.factories import (
    commercial_price_factory,
    price_amount_factory,
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


@pytest.mark.django_db
def test_navbar_cart_fragment_does_not_create_empty_cart(
    client,
):
    customer = _login_customer(
        client=client,
    )

    response = client.get(
        reverse(
            "business_portal:navbar_cart_fragment"
        )
    )

    assert response.status_code == 200

    navbar_cart = response.context[
        "navbar_cart"
    ]

    assert navbar_cart.line_count == 0
    assert navbar_cart.lines == ()
    # Empty: straight to the order, to add from its search.
    assert navbar_cart.empty_action_url == reverse(
        "business_portal:cart"
    )

    assert not BusinessCart.objects.filter(
        customer=customer,
    ).exists()


@pytest.mark.django_db
def test_navbar_cart_fragment_reads_customer_cart(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
        weight_per_unit=5000,
    )

    offer = standard_business_offer_factory(
        product=product,
    )

    line = add_catalog_offer_to_cart(
        customer=customer,
        product=product,
        commercial_price_id=offer.pk,
        quantity=3,
    )

    response = client.get(
        reverse(
            "business_portal:navbar_cart_fragment"
        )
    )

    assert response.status_code == 200

    navbar_cart = response.context[
        "navbar_cart"
    ]

    assert navbar_cart.line_count == 1

    navbar_line = navbar_cart.lines[0]

    assert navbar_line.line_id == line.id
    assert navbar_line.quantity == 3

    # Little room: the name and the weight only, no number or unit.
    assert not navbar_line.label.startswith("#")
    assert "/" not in navbar_line.label
    assert navbar_line.label.endswith(" g")

    # Read-only in the navbar: the quantity shown, changed on the cart's page.
    assert navbar_line.line_view.aside == "× 3"
    html = response.content.decode()
    assert "data-navbar-cart-quantity-form" not in html
    assert "× 3" in html

    assert navbar_line.remove_url == reverse(
        "business_portal:remove_cart_line",
        kwargs={
            "cart_line_id": line.id,
        },
    )


@pytest.mark.django_db
def test_navbar_cart_uses_current_batch_offer_metadata(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
        weight_per_unit=5000,
    )

    standard_business_offer_factory(
        product=product,
    )

    batch = batch_factory(
        product=product,
        today=TODAY,
        quantity=10,
    )

    offer = commercial_price_factory(
        product=product,
        batch=batch,
        channel=CommercialPrice.Channel.BUSINESS,
        reason=CommercialPrice.Reason.SHORT_DATED,
        enabled=True,
    )

    price_amount_factory(
        commercial_price=offer,
        price=Decimal("7.50"),
    )

    add_catalog_offer_to_cart(
        customer=customer,
        product=product,
        commercial_price_id=offer.pk,
        quantity=2,
    )

    response = client.get(
        reverse(
            "business_portal:navbar_cart_fragment"
        )
    )

    assert response.status_code == 200

    navbar_cart = response.context[
        "navbar_cart"
    ]

    navbar_line = navbar_cart.lines[0]

    assert navbar_line.metadata == (
        "Short dated",
        "€7.50",
    )


@pytest.mark.django_db
def test_navbar_cart_does_not_show_another_customers_cart(
    client,
):
    customer = _login_customer(
        client=client,
    )

    other_customer = customer_factory(
        name="Other Customer",
        email="other@example.com",
    )

    product = product_factory(
        name="Apple",
    )

    offer = standard_business_offer_factory(
        product=product,
    )

    add_catalog_offer_to_cart(
        customer=other_customer,
        product=product,
        commercial_price_id=offer.pk,
        quantity=4,
    )

    response = client.get(
        reverse(
            "business_portal:navbar_cart_fragment"
        )
    )

    assert response.status_code == 200

    navbar_cart = response.context[
        "navbar_cart"
    ]

    assert navbar_cart.line_count == 0
    assert navbar_cart.lines == ()

    assert not BusinessCart.objects.filter(
        customer=customer,
    ).exists()


@pytest.mark.django_db
def test_navbar_cart_fragment_requires_login(
    client,
):
    response = client.get(
        reverse(
            "business_portal:navbar_cart_fragment"
        )
    )

    assert response.status_code == 302
