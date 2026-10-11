"""Add batch for a product with several variants: which one is it?"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from accounts.tests.factories import full_staff_user_factory
from inventory.models import InventoryBatch
from ops_portal.inventory.forms import BatchForm
from ops_portal.inventory.pricing_forms import PRICING_STATUS_INACTIVE
from products.services import set_variant_active
from products.tests.factories import product_factory, variant_factory

BEST_BEFORE = f"{timezone.localdate() + timedelta(days=60):%Y-%m-%d}"


def _data(product, **extra):
    return {
        "product": str(product.pk),
        "quantity": "10",
        "best_before": BEST_BEFORE,
        "location": "Shelf A1",
        **extra,
    }


@pytest.fixture
def hoodie():
    product = product_factory(name="Hoodie")
    variant_factory(product=product, label="M", first_label="S")

    return product


@pytest.mark.django_db
def test_a_product_with_variants_needs_one_chosen(hoodie):
    form = BatchForm(data=_data(hoodie))

    assert not form.is_valid()
    assert "variant" in form.errors


@pytest.mark.django_db
def test_the_chosen_variant_goes_with_the_batch(hoodie):
    medium = hoodie.variants.get(label="M")

    form = BatchForm(data=_data(hoodie, variant=str(medium.pk)))

    assert form.is_valid(), form.errors
    assert form.cleaned_data["variant"] == medium


@pytest.mark.django_db
def test_a_variant_of_another_product_is_refused(hoodie):
    other = product_factory(name="T-shirt")
    variant_factory(product=other, label="M", first_label="S")

    form = BatchForm(
        data=_data(hoodie, variant=str(other.variants.get(label="M").pk))
    )

    assert not form.is_valid()
    assert "variant" in form.errors


@pytest.mark.django_db
def test_the_only_variant_on_sale_needs_no_choice(hoodie):
    set_variant_active(variant=hoodie.variants.get(label="M"), active=False)

    form = BatchForm(data=_data(hoodie))

    assert form.is_valid(), form.errors
    assert form.cleaned_data["variant"] == hoodie.variants.get(label="S")


@pytest.mark.django_db
def test_a_product_with_one_variant_shows_no_choice():
    apple = product_factory(name="Apple")

    form = BatchForm(data=_data(apple))

    assert form.is_valid(), form.errors
    assert form.cleaned_data["variant"] is None
    assert form.variant_groups == ()


@pytest.mark.django_db
def test_the_page_draws_the_chosen_product_variants(client, hoodie):
    client.force_login(full_staff_user_factory())

    response = client.get(
        f"{reverse('ops_inventory:create')}?product={hoodie.pk}"
    )
    content = response.content.decode()

    (group,) = response.context["form"].variant_groups
    assert group.shown is True
    assert [choice.text for choice in group.choices] == ["S", "M"]
    assert f'data-batch-variant-for="{hoodie.pk}"' in content


@pytest.mark.django_db
def test_adding_a_batch_of_a_variant(client, hoodie):
    client.force_login(full_staff_user_factory())
    medium = hoodie.variants.get(label="M")

    response = client.post(
        reverse("ops_inventory:create"),
        _data(
            hoodie,
            variant=str(medium.pk),
            business_status=PRICING_STATUS_INACTIVE,
            retail_status=PRICING_STATUS_INACTIVE,
        ),
    )

    assert response.status_code == 302
    assert InventoryBatch.objects.get().variant == medium
