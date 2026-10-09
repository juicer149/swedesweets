from __future__ import annotations

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from accounts.models import CustomerMembership
from accounts.tests.factories import (
    customer_user_factory,
    full_staff_user_factory,
    restricted_staff_user_factory,
)
from business.services import create_order
from business.tests.factories import standard_business_offer_factory
from customers.tests.factories import customer_factory
from inventory.tests.conftest import TODAY
from inventory.tests.factories import batch_factory
from orders.datatypes import OrderLineInput
from products.tests.factories import product_factory


@pytest.mark.django_db
def test_dashboard_renders_title_and_actions(client):
    client.force_login(full_staff_user_factory())

    response = client.get(reverse("ops_dashboard"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Ops dashboard" in content
    assert f'href="{reverse("ops_orders:create")}"' in content
    assert f'href="{reverse("ops_inventory:create")}"' in content


@pytest.mark.django_db
def test_dashboard_for_restricted_staff_has_only_add_batch(client):
    client.force_login(restricted_staff_user_factory())

    response = client.get(reverse("ops_dashboard"))
    content = response.content.decode()

    assert response.status_code == 200
    assert f'href="{reverse("ops_orders:create")}"' not in content
    assert f'href="{reverse("ops_inventory:create")}"' in content


@pytest.mark.django_db
def test_dashboard_queue_is_a_row_that_slides_open_to_its_items(client):
    product = product_factory(name="Apple", internal_number=402)
    standard_business_offer_factory(product=product)
    batch_factory(product=product, today=TODAY, quantity=100)
    order = create_order(
        customer=customer_factory(email="dashboard@example.com"),
        lines=[OrderLineInput.units(product=product, quantity=3)],
    )
    client.force_login(full_staff_user_factory())

    response = client.get(reverse("ops_dashboard"))
    content = response.content.decode()

    placed = next(q for q in response.context["dashboard_queues"] if q.key == "placed")
    assert placed.count == 1
    assert placed.items[0].href == reverse(
        "ops_orders:pack", kwargs={"order_id": order.pk}
    )
    assert 'data-smooth-group="dashboard-queues"' in content
    assert "Placed orders" in content
    assert "dashboard-queue__count--warning" in content


@pytest.mark.django_db
def test_dashboard_lists_shops_waiting_to_fill_in_their_details(client):
    customer_factory(email="complete@example.fr")
    waiting = customer_factory(
        name="Café Blanc",
        email="cafe@example.fr",
        phone_number="",
        city="",
        address_line="",
    )
    customer_user_factory(customer=waiting, username="cafe@example.fr")
    CustomerMembership.objects.filter(customer=waiting).update(
        created_at=timezone.now() - timedelta(days=3)
    )
    customer_factory(name="No Login", email="nologin@example.fr", city="")
    client.force_login(full_staff_user_factory())

    response = client.get(reverse("ops_dashboard"))

    queue = next(
        q for q in response.context["dashboard_queues"]
        if q.key == "waiting-for-details"
    )
    assert queue.title == "Waiting for shop details"
    assert queue.count == 2
    assert [item.title for item in queue.items] == ["Café Blanc", "No Login"]
    assert queue.items[0].meta == "Invited 3 days ago · cafe@example.fr"
    assert queue.items[1].meta.startswith("No login yet")
    assert queue.items[0].href == reverse(
        "ops_customers:detail", kwargs={"customer_pk": waiting.pk}
    )


@pytest.mark.django_db
def test_restricted_staff_do_not_see_shops_waiting_for_details(client):
    customer_factory(phone_number="", city="", address_line="")
    client.force_login(restricted_staff_user_factory())

    response = client.get(reverse("ops_dashboard"))

    assert all(
        q.key != "waiting-for-details"
        for q in response.context["dashboard_queues"]
    )
