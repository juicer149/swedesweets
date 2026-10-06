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
    assert "Product details" in content
    assert "data-smooth" in content

    edit_url = reverse("ops_products:edit", kwargs={"product_pk": product.pk})
    assert f'href="{edit_url}"' in content
    assert f'href="{reverse("ops_products:index")}"' in content
