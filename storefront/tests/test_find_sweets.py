from __future__ import annotations

import pytest
from django.urls import reverse

from customers.services import deactivate_customer, update_customer_listing
from customers.tests.factories import customer_factory


def _listed(**kwargs):
    store = kwargs.pop("store", None)
    customer = customer_factory(**kwargs)
    update_customer_listing(
        customer=customer,
        listed_publicly=True,
        store_address_line=store[0] if store else "",
        store_city=store[1] if store else "",
    )
    return customer


@pytest.mark.django_db
def test_lists_active_shops_that_chose_to_be_listed(client):
    _listed(name="Café Blanc", email="blanc@example.fr")
    customer_factory(name="Hidden Shop", email="hidden@example.fr")
    gone = _listed(name="Closed Shop", email="closed@example.fr")
    deactivate_customer(customer=gone)

    response = client.get(reverse("public_site:find_sweets"))
    html = response.content.decode()

    assert response.status_code == 200
    assert [shop.name for shop in response.context["shops"]] == ["Café Blanc"]
    assert "Hidden Shop" not in html
    assert 'target="_blank"' in html


@pytest.mark.django_db
def test_store_address_wins_over_the_delivery_address(client):
    _listed(
        name="Kiosque",
        email="kiosque@example.fr",
        store=("2 Place du Lac", "Annecy"),
    )

    (shop,) = client.get(reverse("public_site:find_sweets")).context["shops"]

    assert shop.address == "2 Place du Lac, Annecy, France"
    assert "Annecy" in shop.maps_href


@pytest.mark.django_db
def test_a_half_store_address_is_refused():
    from customers.errors import InvalidCustomerData

    customer = customer_factory(email="half@example.fr")

    with pytest.raises(InvalidCustomerData):
        update_customer_listing(
            customer=customer,
            listed_publicly=True,
            store_address_line="2 Place du Lac",
        )


@pytest.mark.django_db
def test_page_is_open_to_anonymous_visitors_with_nobody_listed(client):
    response = client.get(reverse("public_site:find_sweets"))

    assert response.status_code == 200
    assert "No shops are listed yet." in response.content.decode()
