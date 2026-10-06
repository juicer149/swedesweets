from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.tests.factories import customer_user_factory
from customers.tests.factories import customer_factory


@pytest.mark.django_db
def test_store_edit_page_shows_form_and_actions(client):
    client.force_login(
        customer_user_factory(
            customer=customer_factory(email="store@example.com"),
        )
    )

    response = client.get(reverse("business_portal:edit_store"))
    content = response.content.decode()

    assert response.status_code == 200
    assert 'name="email"' in content
    assert 'value="store@example.com"' in content
    assert f'href="{reverse("business_portal:index")}"' in content


@pytest.mark.django_db
def test_order_history_on_phones_is_link_rows(client):
    customer = customer_factory(email="rows@example.fr")
    client.force_login(customer_user_factory(customer=customer))

    response = client.get(reverse("business_portal:index"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "data-order-card-list" in content
    assert 'class="lines mobile-lines"' in content
    assert "mobile-card" not in content



@pytest.mark.django_db
def test_store_edit_saves_the_find_sweets_listing(client):
    customer = customer_factory(email="listing@example.fr")
    client.force_login(customer_user_factory(customer=customer))

    response = client.post(
        reverse("business_portal:edit_store"),
        {
            "name": customer.name,
            "email": customer.email,
            "phone_number": customer.phone_number,
            "country": customer.country,
            "city": customer.city,
            "address_line": customer.address_line,
            "listed_publicly": "on",
            "store_address_line": "2 Place du Lac",
            "store_city": "Annecy",
        },
    )

    assert response.status_code == 302
    customer.refresh_from_db()
    assert customer.listed_publicly is True
    assert customer.public_address == "2 Place du Lac, Annecy, France"


@pytest.mark.django_db
def test_store_edit_asks_for_both_parts_of_the_store_address(client):
    customer = customer_factory(email="half-listing@example.fr")
    client.force_login(customer_user_factory(customer=customer))

    response = client.post(
        reverse("business_portal:edit_store"),
        {
            "name": customer.name,
            "email": customer.email,
            "phone_number": customer.phone_number,
            "country": customer.country,
            "city": customer.city,
            "address_line": customer.address_line,
            "store_address_line": "2 Place du Lac",
        },
    )

    assert response.status_code == 200
    assert "store_city" in response.context["form"].errors
