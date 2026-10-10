from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.tests.factories import (
    customer_user_factory,
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
)
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


def _stocked_offer(
    *,
    name: str,
    quantity: int,
) -> CommercialPrice:
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
    )

    return offer


def _cart_lines(
    customer,
):
    return BusinessCart.objects.get(
        customer=customer,
    ).cart.lines.all()


@pytest.mark.django_db
def test_cart_offers_the_catalog_in_its_quick_add(
    client,
):
    _login_customer(
        client=client,
    )
    few = _stocked_offer(
        name="Apple",
        quantity=4,
    )
    plenty = _stocked_offer(
        name="Pear",
        quantity=30,
    )

    response = client.get(
        reverse("business_portal:cart")
    )
    content = response.content.decode()

    options = {
        option.commercial_price_id: option
        for option in response.context["quick_add_options"]
    }

    assert response.status_code == 200
    assert "data-cart-quick-add" in content
    assert options[few.pk].package_label == "2000 g / Box"
    # How many are left only when few are (the catalog's rule).
    assert options[few.pk].stock_label == "Only 4 left"
    assert options[plenty.pk].stock_label == ""


@pytest.mark.django_db
def test_quick_add_is_there_when_the_cart_is_empty(
    client,
):
    _login_customer(
        client=client,
    )
    _stocked_offer(
        name="Apple",
        quantity=10,
    )

    response = client.get(
        reverse("business_portal:cart")
    )
    content = response.content.decode()

    assert response.context["cart_lines"] == ()
    assert "data-cart-quick-add" in content


@pytest.mark.django_db
def test_quick_add_puts_one_unit_in_the_cart_and_comes_back(
    client,
):
    customer = _login_customer(
        client=client,
    )
    offer = _stocked_offer(
        name="Apple",
        quantity=10,
    )
    url = reverse("business_portal:add_cart_offer")

    response = client.post(
        url,
        {"commercial_price_id": str(offer.pk)},
    )

    assert response.status_code == 302
    assert response.url == reverse("business_portal:cart")
    assert [
        (line.commercial_price_id, line.quantity)
        for line in _cart_lines(customer)
    ] == [(offer.pk, 1)]

    # Again: the same line, one more.
    client.post(
        url,
        {"commercial_price_id": str(offer.pk)},
    )

    assert [
        line.quantity
        for line in _cart_lines(customer)
    ] == [2]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "raw_value",
    ["", "abc", "999999"],
)
def test_quick_add_without_a_valid_offer_adds_nothing(
    client,
    raw_value,
):
    customer = _login_customer(
        client=client,
    )

    response = client.post(
        reverse("business_portal:add_cart_offer"),
        {"commercial_price_id": raw_value},
    )

    assert response.status_code == 302
    assert not BusinessCart.objects.filter(
        customer=customer,
    ).exists()


@pytest.mark.django_db
def test_quick_add_refuses_a_retail_offer(
    client,
):
    customer = _login_customer(
        client=client,
    )
    product = product_factory(
        name="Apple",
    )
    retail_offer = commercial_price_factory(
        product=product,
        batch=None,
        channel=CommercialPrice.Channel.RETAIL,
        enabled=True,
    )

    client.post(
        reverse("business_portal:add_cart_offer"),
        {"commercial_price_id": str(retail_offer.pk)},
    )

    assert not BusinessCart.objects.filter(
        customer=customer,
        cart__lines__isnull=False,
    ).exists()


@pytest.mark.django_db
def test_quick_add_requires_post(
    client,
):
    _login_customer(
        client=client,
    )

    response = client.get(
        reverse("business_portal:add_cart_offer")
    )

    assert response.status_code == 405
