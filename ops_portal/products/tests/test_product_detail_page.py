from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.tests.factories import full_staff_user_factory
from inventory.tests.conftest import TODAY
from inventory.tests.factories import batch_factory
from products.tests.factories import product_factory


@pytest.mark.django_db
def test_product_detail_shows_stock_batches_and_edit(client):
    client.force_login(full_staff_user_factory())

    product = product_factory(
        name="Apple",
        internal_number=501,
    )
    batch = batch_factory(
        product=product,
        today=TODAY,
        batch_id="B-501",
        quantity=12,
    )

    response = client.get(
        reverse("ops_products:detail", kwargs={"product_pk": product.pk}),
    )
    content = response.content.decode()

    assert response.status_code == 200
    assert response.context["status_key"] == "active"

    (row,) = response.context["batch_rows"]
    assert row.batch_id == "B-501"
    assert "Shelf A1" in row.meta

    batch_url = reverse("ops_inventory:detail", kwargs={"batch_pk": batch.pk})
    assert f'href="{batch_url}"' in content
    assert "data-tabs" in content
    assert "demand" not in response.context
    assert "Edit catalog" not in content

    # Each tab's button opens the same tab of the edit form.
    edit_url = reverse("ops_products:edit", kwargs={"product_pk": product.pk})
    assert f'href="{edit_url}#product"' in content
    assert f'href="{edit_url}#pricing"' in content

    add_batch_url = f"{reverse('ops_inventory:create')}?product={product.pk}"
    assert f'href="{add_batch_url}"' in content
    assert f'href="{reverse("ops_products:index")}"' in content


@pytest.mark.django_db
def test_add_batch_link_preselects_the_product(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Apple", internal_number=502)

    response = client.get(
        reverse("ops_inventory:create"),
        {"product": product.pk},
    )

    assert response.status_code == 200
    assert response.context["form"].initial["product"] == product.pk


@pytest.mark.django_db
def test_product_edit_form_has_the_same_tabs_as_the_links(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Apple", internal_number=503)

    response = client.get(
        reverse("ops_products:edit", kwargs={"product_pk": product.pk}),
    )
    content = response.content.decode()

    assert response.status_code == 200
    assert [tab.key for tab in response.context["page_tabs"]] == [
        "product",
        "catalog",
        "pricing",
    ]
    # The detail page links to #product and #pricing; tabs.js opens them.
    assert 'data-tab="product"' in content
    assert 'data-tab="pricing"' in content
    assert "data-dirty-form" in content
    assert 'name="business_eur"' in content


@pytest.mark.django_db
def test_product_create_form_renders(client):
    client.force_login(full_staff_user_factory())

    response = client.get(reverse("ops_products:create"))

    assert response.status_code == 200
    assert 'name="weight_per_unit"' in response.content.decode()


@pytest.mark.parametrize(
    ("available", "active", "state"),
    [
        (20, True, "on"),
        (10, True, "on"),
        (9, True, "warn"),
        (7, True, "warn"),
        (6, True, "off"),
        (1, True, "off"),
        (0, True, "none"),
        (20, False, "none"),
    ],
)
def test_available_is_coloured_by_how_much_is_left(available, active, state):
    from ops_portal.products.detail_viewmodels import ProductStockSummary
    from products.models import Product

    stock = ProductStockSummary(
        product=Product(active=active),
        batch_count=1,
        physical_quantity=available,
        reserved_quantity=0,
        available_quantity=available,
    )

    assert stock.available_state == state
