from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.tests.factories import full_staff_user_factory
from business.services import create_order
from business.tests.factories import standard_business_offer_factory
from customers.models import StoreListing
from customers.tests.factories import customer_factory
from inventory.tests.conftest import TODAY
from inventory.tests.factories import batch_factory
from orders.datatypes import OrderLineInput
from products.tests.factories import product_factory


@pytest.fixture
def staff_client(client):
    client.force_login(full_staff_user_factory())
    return client


@pytest.fixture
def customer():
    return customer_factory(name="Café Blanc", email="cafe@example.fr")


@pytest.mark.django_db
def test_list_is_rows_with_a_search_and_no_table(staff_client, customer):
    response = staff_client.get(reverse("ops_customers:index"))
    content = response.content.decode()

    assert response.status_code == 200
    (row,) = response.context["customer_rows"]
    assert row.meta == "Chamonix-Mont-Blanc, France"
    assert row.icon == "users"
    assert 'class="lines"' in content
    assert "data-table" not in content
    assert "mobile-card" not in content

    (option,) = response.context["quick_jump_search"].options
    assert option.label == "Café Blanc · Chamonix-Mont-Blanc"
    assert option.url == row.detail_href
    assert 'data-quick-jump="true"' in content


@pytest.mark.django_db
def test_detail_has_contact_rows_orders_tab_and_edit(staff_client, customer):
    product = product_factory(name="Apple", internal_number=601)
    standard_business_offer_factory(product=product)
    batch_factory(product=product, today=TODAY, quantity=100)
    order = create_order(
        customer=customer,
        lines=[OrderLineInput.units(product=product, quantity=3)],
    )

    response = staff_client.get(
        reverse("ops_customers:detail", kwargs={"customer_pk": customer.pk}),
    )
    content = response.content.decode()

    assert response.status_code == 200
    assert response.context["status_key"] == "active"
    assert response.context["orders_label"] == "1 order"
    assert [tab.key for tab in response.context["page_tabs"]] == [
        "customer",
        "orders",
    ]

    assert 'href="mailto:cafe@example.fr"' in content
    assert "icon-rows--tight" in content

    (row,) = response.context["order_rows"]
    assert row.title == f"#{order.pk}"
    order_url = reverse("ops_orders:detail", kwargs={"order_id": order.pk})
    assert f'href="{order_url}"' in content

    edit_url = reverse("ops_customers:edit", kwargs={"customer_pk": customer.pk})
    assert f'href="{edit_url}"' in content
    assert f'href="{reverse("ops_customers:index")}"' in content


@pytest.mark.django_db
def test_detail_without_orders_says_so(staff_client, customer):
    response = staff_client.get(
        reverse("ops_customers:detail", kwargs={"customer_pk": customer.pk}),
    )

    assert "This customer has no orders yet." in response.content.decode()


@pytest.mark.django_db
def test_edit_form_is_calm_and_dirty_aware(staff_client, customer):
    response = staff_client.get(
        reverse("ops_customers:edit", kwargs={"customer_pk": customer.pk}),
    )
    content = response.content.decode()

    assert response.status_code == 200
    assert response.context["title"] == "Edit Café Blanc"
    assert "data-dirty-form" in content
    assert 'name="address_line"' in content
    assert "form_context_card" not in content
    assert "form-context" not in content


@pytest.mark.django_db
def test_create_form_renders_with_a_plain_title(staff_client):
    response = staff_client.get(reverse("ops_customers:create"))

    assert response.status_code == 200
    assert "status_key" not in response.context
    assert 'name="email"' in response.content.decode()


@pytest.mark.django_db
def test_edit_lists_the_shop_on_find_sweets(staff_client, customer):
    url = reverse("ops_customers:edit", kwargs={"customer_pk": customer.pk})

    assert 'name="is_listed"' in staff_client.get(url).content.decode()

    response = staff_client.post(
        url,
        {
            "name": "Café Blanc",
            "email": "cafe@example.fr",
            "phone_number": "+33 6 12 34 56 78",
            "country": "FR",
            "city": "Chamonix-Mont-Blanc",
            "address_line": "1 Rue du Lac",
            "is_listed": "true",
            "store_address_line": "2 Place du Lac",
            "store_city": "Annecy",
        },
    )

    assert response.status_code == 302
    listing = StoreListing.objects.get(customer=customer)
    assert listing.is_listed
    assert listing.public_city == "Annecy"


@pytest.mark.django_db
def test_create_form_has_no_find_sweets_fields(staff_client):
    response = staff_client.get(reverse("ops_customers:create"))

    assert 'name="is_listed"' not in response.content.decode()


@pytest.mark.django_db
def test_detail_footer_shows_status_and_listing(staff_client, customer):
    response = staff_client.get(
        reverse("ops_customers:detail", kwargs={"customer_pk": customer.pk}),
    )
    content = response.content.decode()

    assert "status-text--success facts__status\">Active" in content
    assert "status-text--muted facts__status\">Not listed" in content
