"""A shop invited by mail fills in its details before anything else, and
then orders as usual."""

from __future__ import annotations

import pytest
from django.test import override_settings
from django.urls import reverse

from accounts.tests.factories import customer_user_factory
from customers.services import create_customer
from customers.tests.factories import customer_factory


@pytest.fixture
def new_shop_client(client):
    customer = create_customer(
        name="Café Blanc",
        email="cafe@example.fr",
        phone_number="",
        country="FR",
        city="",
        address_line="",
    )
    client.force_login(customer_user_factory(customer=customer))
    return client, customer


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en")
def test_portal_pages_lead_to_the_details_form_until_filled_in(new_shop_client):
    client, _customer = new_shop_client

    for name in ("business_portal:index", "business_portal:catalog"):
        response = client.get(reverse(name))
        assert response.status_code == 302
        assert response.url == reverse("business_portal:edit_store")

    response = client.get(reverse("business_portal:edit_store"))
    assert response.status_code == 200
    assert "Complete your shop details" in response.content.decode()


@pytest.mark.django_db
def test_complete_shop_uses_the_portal_as_usual(client):
    customer = customer_factory()
    client.force_login(customer_user_factory(customer=customer))

    assert customer.is_complete
    assert client.get(reverse("business_portal:index")).status_code == 200


@pytest.mark.django_db
def test_incomplete_shop_is_not_on_find_sweets():
    from customers.selectors import list_listed_stores
    from customers.services import update_store_listing

    customer = create_customer(
        name="Café Blanc",
        email="cafe@example.fr",
        phone_number="",
        country="FR",
        city="",
        address_line="",
    )
    update_store_listing(customer=customer, is_listed=True)

    assert not list_listed_stores().filter(customer=customer).exists()
