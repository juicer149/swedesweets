from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.tests.factories import full_staff_user_factory
from inventory.tests.conftest import TODAY
from inventory.tests.factories import batch_factory
from products.tests.factories import product_factory


@pytest.fixture
def staff_client(client):
    client.force_login(full_staff_user_factory())
    return client


@pytest.fixture
def batch():
    return batch_factory(
        product=product_factory(name="Apple", internal_number=601),
        today=TODAY,
        batch_id="B-601",
        quantity=8,
    )


def _batch_url(name, batch):
    return reverse(name, kwargs={"batch_pk": batch.pk})


@pytest.mark.django_db
def test_batch_detail_has_tabs_product_link_and_actions(staff_client, batch):
    response = staff_client.get(_batch_url("ops_inventory:detail", batch))
    content = response.content.decode()

    assert response.status_code == 200
    assert [tab.key for tab in response.context["page_tabs"]] == [
        "batch",
        "pricing",
        "usage",
    ]
    assert response.context["stock"].available_info.level == "running_low"

    product_url = reverse(
        "ops_products:detail",
        kwargs={"product_pk": batch.product_id},
    )
    assert f'href="{product_url}"' in content
    assert f'href="{_batch_url("ops_inventory:edit", batch)}#batch"' in content
    assert f'href="{_batch_url("ops_inventory:edit", batch)}#pricing"' in content
    assert f'href="{_batch_url("ops_inventory:close", batch)}"' in content
    assert f'href="{reverse("ops_inventory:index")}"' in content


@pytest.mark.django_db
def test_batch_edit_form_has_the_tabs_the_detail_links_to(staff_client, batch):
    response = staff_client.get(_batch_url("ops_inventory:edit", batch))
    content = response.content.decode()

    assert response.status_code == 200
    assert response.context["title"] == "Edit batch B-601"
    assert [tab.key for tab in response.context["page_tabs"]] == [
        "batch",
        "pricing",
    ]
    assert 'data-tab="pricing"' in content
    assert 'name="business_eur"' in content
    assert "data-dirty-form" in content


@pytest.mark.django_db
def test_new_batch_form_renders_with_the_product_field(staff_client):
    response = staff_client.get(reverse("ops_inventory:create"))

    assert response.status_code == 200
    assert 'name="product"' in response.content.decode()


@pytest.mark.django_db
def test_close_batch_page_shows_the_batch_and_a_red_button(staff_client, batch):
    response = staff_client.get(_batch_url("ops_inventory:close", batch))
    content = response.content.decode()

    assert response.status_code == 200
    assert response.context["quantity_label"]
    assert "button--tone-danger" in content


@pytest.mark.django_db
def test_inventory_lists_show_tables_and_coloured_phone_rows(staff_client, batch):
    views = (
        ({}, "inventory_rows"),
        ({"view": "products"}, "product_rows"),
    )

    for params, row_key in views:
        response = staff_client.get(reverse("ops_inventory:index"), params)
        content = response.content.decode()

        assert response.status_code == 200
        assert "data-table" in content
        assert "mobile-lines" in content
        assert response.context[row_key]
        # Phone rows carry the stock colour of the table cells.
        assert "line__aside quantity-text" in content


@pytest.mark.django_db
def test_stock_by_product_shows_the_unit_but_does_not_sort_by_it(
    staff_client,
    batch,
):
    response = staff_client.get(
        reverse("ops_inventory:index") + "?view=products"
    )

    headers = {sort.field: sort for sort in response.context["table_sorts"]}

    assert headers["unit"].sortable is False
    assert headers["product"].sortable is True
    assert "unit" not in [
        sort.field for sort in response.context["mobile_sort_fields"]
    ]
