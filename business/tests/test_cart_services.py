from __future__ import annotations

import pytest

from business.cart_services import (
    get_or_create_customer_cart,
)
from business.models import BusinessCart
from carts.models import Cart
from carts.services import create_cart
from common.channels import SalesChannel
from customers.models import Customer


def _customer(
    *,
    email: str,
) -> Customer:
    return Customer.objects.create(
        name="Business Customer",
        email=email,
        phone_number="+33612345678",
        country="FR",
        city="Annecy",
        address_line="10 Rue de Test",
    )


@pytest.mark.django_db
def test_get_or_create_customer_cart_creates_business_cart():
    customer = _customer(
        email="first@example.com",
    )

    cart = get_or_create_customer_cart(
        customer=customer,
    )

    assert cart.channel == SalesChannel.BUSINESS
    assert cart.lines.count() == 0

    business_cart = BusinessCart.objects.get(
        customer=customer,
    )

    assert business_cart.cart == cart


@pytest.mark.django_db
def test_get_or_create_customer_cart_returns_existing_cart():
    customer = _customer(
        email="existing@example.com",
    )

    first = get_or_create_customer_cart(
        customer=customer,
    )
    second = get_or_create_customer_cart(
        customer=customer,
    )

    assert second.pk == first.pk
    assert Cart.objects.count() == 1
    assert BusinessCart.objects.count() == 1


@pytest.mark.django_db
def test_different_customers_have_different_carts():
    first_customer = _customer(
        email="first@example.com",
    )
    second_customer = _customer(
        email="second@example.com",
    )

    first_cart = get_or_create_customer_cart(
        customer=first_customer,
    )
    second_cart = get_or_create_customer_cart(
        customer=second_customer,
    )

    assert first_cart.pk != second_cart.pk
    assert Cart.objects.count() == 2
    assert BusinessCart.objects.count() == 2


@pytest.mark.django_db
def test_customer_can_receive_new_cart_after_previous_cart_is_deleted():
    customer = _customer(
        email="replacement@example.com",
    )

    first_cart = get_or_create_customer_cart(
        customer=customer,
    )
    first_cart_id = first_cart.pk

    first_cart.delete()

    assert not BusinessCart.objects.filter(
        customer=customer,
    ).exists()

    second_cart = get_or_create_customer_cart(
        customer=customer,
    )

    assert second_cart.pk != first_cart_id
    assert second_cart.channel == SalesChannel.BUSINESS
    assert BusinessCart.objects.get(
        customer=customer,
    ).cart == second_cart


@pytest.mark.django_db
def test_customer_cart_rejects_non_business_cart():
    customer = _customer(
        email="invalid@example.com",
    )
    cart = create_cart(
        channel=SalesChannel.RETAIL,
    )

    BusinessCart.objects.create(
        customer=customer,
        cart=cart,
    )

    with pytest.raises(
        RuntimeError,
        match="business cart invariant violated",
    ):
        get_or_create_customer_cart(
            customer=customer,
        )
