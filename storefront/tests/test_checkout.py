from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from carts.models import Cart
from carts.services import create_cart
from common.channels import SalesChannel
from inventory.services import create_batch
from orders.models import Order
from retail.models import RetailCheckoutSession
from retail.services import (
    add_retail_cart_line,
    start_retail_payment,
)
from retail.tests.factories import (
    retail_postal_area_factory,
    retail_product_price_factory,
)
from storefront.cart import (
    COOKIE_NAME,
    COOKIE_SALT,
)
from storefront.checkout_session import CHECKOUT_IDS_SESSION_KEY


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


def _details(**overrides: str) -> dict[str, str]:
    return {
        "first_name": "Marie",
        "last_name": "Dupont",
        "email": "marie@example.com",
        "phone_number": "+33612345678",
        "address_line": "10 Rue de Test",
        "postal_code": "74000",
        "city": "Annecy",
    } | overrides


@pytest.fixture
def cart(client, db):
    retail_postal_area_factory()

    offer = retail_product_price_factory(
        enabled=True,
        price=Decimal("10.00"),
    )
    create_batch(
        batch_id="CHECKOUT-001",
        product=offer.product,
        quantity=10,
        best_before=timezone.localdate() + timedelta(days=60),
        location="Shelf A1",
    )

    cart = create_cart(
        channel=SalesChannel.RETAIL,
    )
    add_retail_cart_line(
        cart=cart,
        commercial_price_id=offer.pk,
        quantity=2,
    )

    _set_signed_retail_cart_cookie(
        client,
        cart=cart,
    )

    return cart


def _submit_details(client, **overrides: str):
    return client.post(
        reverse("storefront:checkout"),
        _details(**overrides),
    )


@pytest.mark.django_db
def test_checkout_without_cart_redirects_to_cart(client):
    response = client.get(
        reverse("storefront:checkout")
    )

    assert response.status_code == 302
    assert response.url == reverse("storefront:cart")


@pytest.mark.django_db
def test_checkout_form_renders_with_cart_summary(client, cart):
    response = client.get(
        reverse("storefront:checkout")
    )

    content = response.content.decode()

    assert response.status_code == 200
    assert 'name="first_name"' in content
    assert "€20.00" in content


@pytest.mark.django_db
def test_valid_details_create_checkout_and_keep_cart(client, cart):
    response = _submit_details(client)

    checkout = RetailCheckoutSession.objects.get()

    assert response.status_code == 302
    assert response.url == reverse(
        "storefront:checkout_review",
        kwargs={
            "checkout_id": checkout.pk,
        },
    )
    assert checkout.order.status == Order.Status.DRAFT
    assert checkout.order.buyer_name_snapshot == "Marie Dupont"
    assert checkout.cart_id == cart.pk
    assert Cart.objects.filter(pk=cart.pk).exists()
    assert str(checkout.pk) in client.session[CHECKOUT_IDS_SESSION_KEY]


@pytest.mark.django_db
def test_unsupported_destination_is_a_field_error(client, cart):
    response = _submit_details(
        client,
        postal_code="75001",
        city="Paris",
    )

    assert response.status_code == 200
    assert response.context["form"].has_error("postal_code")
    assert not RetailCheckoutSession.objects.exists()


@pytest.mark.django_db
def test_review_shows_order_to_owning_session(client, cart):
    _submit_details(client)
    checkout = RetailCheckoutSession.objects.get()

    response = client.get(
        reverse(
            "storefront:checkout_review",
            kwargs={
                "checkout_id": checkout.pk,
            },
        )
    )

    content = response.content.decode()

    assert response.status_code == 200
    assert "Marie Dupont" in content
    assert "€20.00" in content


@pytest.mark.django_db
def test_review_is_hidden_from_other_sessions(client, cart):
    _submit_details(client)
    checkout = RetailCheckoutSession.objects.get()

    response = Client().get(
        reverse(
            "storefront:checkout_review",
            kwargs={
                "checkout_id": checkout.pk,
            },
        )
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_resubmitting_details_replaces_unpaid_checkout(client, cart):
    _submit_details(client)
    first = RetailCheckoutSession.objects.get()

    response = _submit_details(
        client,
        first_name="Anne",
    )

    second = RetailCheckoutSession.objects.exclude(pk=first.pk).get()
    first.order.refresh_from_db()

    assert first.order.status == Order.Status.CANCELLED
    assert response.url == reverse(
        "storefront:checkout_review",
        kwargs={
            "checkout_id": second.pk,
        },
    )


@pytest.mark.django_db
def test_payment_in_progress_redirects_to_existing_checkout(client, cart):
    _submit_details(client)
    checkout = RetailCheckoutSession.objects.get()

    start_retail_payment(
        checkout=checkout,
    )

    response = _submit_details(client)

    assert response.status_code == 302
    assert response.url == reverse(
        "storefront:checkout_review",
        kwargs={
            "checkout_id": checkout.pk,
        },
    )
    assert RetailCheckoutSession.objects.count() == 1


@pytest.mark.django_db
def test_details_form_is_prefilled_from_session(client, cart):
    _submit_details(client)

    response = client.get(
        reverse("storefront:checkout")
    )

    assert response.context["form"].initial["email"] == "marie@example.com"


@pytest.mark.django_db
def test_cart_page_links_to_checkout(client, cart):
    response = client.get(
        reverse("storefront:cart")
    )

    assert reverse("storefront:checkout") in response.content.decode()
