from __future__ import annotations

from datetime import timedelta

import pytest

from inventory.errors import InvalidStockOperation
from inventory.models import InventoryBatch
from inventory.services import create_batch
from inventory.tests.conftest import TODAY
from products.tests.factories import product_factory, variant_factory

BEST_BEFORE = TODAY + timedelta(days=60)


def _create(product, **kwargs):
    return create_batch(
        product=product,
        quantity=5,
        best_before=BEST_BEFORE,
        location="Shelf A1",
        today=TODAY,
        **kwargs,
    )


@pytest.mark.django_db
def test_a_batch_of_a_product_with_one_variant_gets_that_variant(apple):
    batch = _create(apple, batch_id="A-1")

    assert batch.variant == apple.variants.get()


@pytest.mark.django_db
def test_a_batch_can_be_of_a_chosen_variant():
    hoodie = product_factory(name="Hoodie")
    medium = variant_factory(product=hoodie, label="M")

    batch = _create(hoodie, variant=medium, batch_id="H-M-1")

    assert batch.variant == medium
    assert batch.product == hoodie


@pytest.mark.django_db
def test_a_product_with_several_variants_needs_one_chosen():
    hoodie = product_factory(name="Hoodie")
    variant_factory(product=hoodie, label="M")

    with pytest.raises(InvalidStockOperation, match="choose which variant"):
        _create(hoodie, batch_id="H-1")

    assert not InventoryBatch.objects.exists()


@pytest.mark.django_db
def test_a_batch_cannot_be_of_another_product_variant(apple, banana):
    with pytest.raises(InvalidStockOperation, match="another product"):
        _create(
            apple,
            variant=banana.variants.get(),
            batch_id="A-1",
        )


@pytest.mark.django_db
def test_a_batch_given_only_its_variant_takes_its_product(apple):
    batch = InventoryBatch.objects.create(
        batch_id="A-1",
        variant=apple.variants.get(),
        quantity=5,
        best_before=BEST_BEFORE,
        location="Shelf A1",
    )

    assert batch.product == apple


@pytest.mark.django_db
def test_moving_a_batch_to_another_product_keeps_the_variant_in_step(
    apple,
    banana,
):
    batch = _create(apple, batch_id="A-1")
    batch.product = banana

    with pytest.raises(InvalidStockOperation, match="another product"):
        batch.save(update_fields=["product"])
