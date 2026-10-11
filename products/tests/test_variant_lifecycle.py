"""Rules 1 and 5-7 (docs/product-variants.md): a variant's weight, pause,
delete and order."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from inventory.services import create_batch
from products.errors import InvalidProductData
from products.services import (
    VariantChange,
    delete_variant,
    reorder_variants,
    save_variants,
    set_variant_active,
    set_variant_weight,
    variant_has_history,
)
from products.tests.factories import product_factory, variant_factory

TODAY = timezone.localdate()


def _stock(variant):
    return create_batch(
        product=variant.product,
        variant=variant,
        quantity=5,
        best_before=TODAY + timedelta(days=60),
        location="Shelf A1",
        today=TODAY,
    )


@pytest.fixture
def hoodie():
    product = product_factory(name="Hoodie")
    variant_factory(product=product, label="M", first_label="S")

    return product


@pytest.mark.django_db
def test_a_new_variant_can_change_weight(hoodie):
    medium = hoodie.variants.get(label="M")

    set_variant_weight(variant=medium, weight_per_unit=450)

    medium.refresh_from_db()
    assert medium.weight_per_unit == 450


@pytest.mark.django_db
def test_a_stocked_variant_keeps_its_weight(hoodie):
    medium = hoodie.variants.get(label="M")
    _stock(medium)

    with pytest.raises(InvalidProductData, match="weight"):
        set_variant_weight(variant=medium, weight_per_unit=450)


@pytest.mark.django_db
def test_a_variant_can_be_paused_while_another_is_on_sale(hoodie):
    medium = hoodie.variants.get(label="M")

    set_variant_active(variant=medium, active=False)

    medium.refresh_from_db()
    assert medium.active is False


@pytest.mark.django_db
def test_the_last_variant_on_sale_cannot_be_paused(hoodie):
    small = hoodie.variants.get(label="S")
    medium = hoodie.variants.get(label="M")
    set_variant_active(variant=medium, active=False)

    with pytest.raises(InvalidProductData, match="pause the product"):
        set_variant_active(variant=small, active=False)


@pytest.mark.django_db
def test_an_unused_variant_can_be_deleted(hoodie):
    medium = hoodie.variants.get(label="M")

    assert variant_has_history(medium) is False

    delete_variant(variant=medium)

    assert list(hoodie.variants.values_list("label", flat=True)) == ["S"]


@pytest.mark.django_db
def test_a_used_variant_can_only_be_paused(hoodie):
    medium = hoodie.variants.get(label="M")
    _stock(medium)

    assert variant_has_history(medium) is True

    with pytest.raises(InvalidProductData, match="pause it instead"):
        delete_variant(variant=medium)


@pytest.mark.django_db
def test_the_last_variant_cannot_be_deleted():
    product = product_factory(name="Sticker")

    with pytest.raises(InvalidProductData, match="at least one variant"):
        delete_variant(variant=product.variants.get())


@pytest.mark.django_db
def test_variants_can_be_reordered(hoodie):
    large = variant_factory(product=hoodie, label="L")
    small = hoodie.variants.get(label="S")
    medium = hoodie.variants.get(label="M")

    reorder_variants(
        product=hoodie,
        variant_ids=[large.pk, small.pk, medium.pk],
    )

    assert list(hoodie.variants.values_list("label", flat=True)) == [
        "L",
        "S",
        "M",
    ]


@pytest.mark.django_db
def test_a_new_order_must_name_every_variant_once(hoodie):
    small = hoodie.variants.get(label="S")

    with pytest.raises(InvalidProductData, match="each of the product"):
        reorder_variants(product=hoodie, variant_ids=[small.pk, small.pk])


def _rows(product):
    return [
        (variant.label, variant.position, variant.active)
        for variant in product.variants.all()
    ]


@pytest.mark.django_db
def test_save_variants_swaps_labels_and_reorders(hoodie):
    small = hoodie.variants.get(label="S")
    medium = hoodie.variants.get(label="M")

    save_variants(
        product=hoodie,
        changes=[
            VariantChange(variant_id=medium.pk, label="S", weight_per_unit=275),
            VariantChange(variant_id=small.pk, label="M", weight_per_unit=275),
        ],
    )

    assert _rows(hoodie) == [("S", 1, True), ("M", 2, True)]
    medium.refresh_from_db()
    assert medium.label == "S"


@pytest.mark.django_db
def test_save_variants_adds_pauses_and_deletes(hoodie):
    small = hoodie.variants.get(label="S")
    medium = hoodie.variants.get(label="M")

    save_variants(
        product=hoodie,
        changes=[
            VariantChange(variant_id=small.pk, label="S", weight_per_unit=275),
            VariantChange(
                variant_id=medium.pk,
                label="M",
                weight_per_unit=275,
                delete=True,
            ),
            VariantChange(
                variant_id=None,
                label="L",
                weight_per_unit=320,
                active=False,
            ),
        ],
    )

    assert _rows(hoodie) == [("S", 1, True), ("L", 2, False)]


@pytest.mark.django_db
def test_save_variants_can_replace_an_unused_only_variant():
    product = product_factory(name="Sticker")
    only = product.variants.get()

    save_variants(
        product=product,
        changes=[
            VariantChange(
                variant_id=only.pk,
                label="",
                weight_per_unit=10,
                delete=True,
            ),
            VariantChange(variant_id=None, label="Large", weight_per_unit=20),
        ],
    )

    assert _rows(product) == [("Large", 1, True)]


@pytest.mark.django_db
def test_save_variants_changes_nothing_when_a_rule_says_no(hoodie):
    small = hoodie.variants.get(label="S")
    medium = hoodie.variants.get(label="M")

    with pytest.raises(InvalidProductData, match="each needs a label"):
        save_variants(
            product=hoodie,
            changes=[
                VariantChange(variant_id=small.pk, label="", weight_per_unit=275),
                VariantChange(variant_id=medium.pk, label="M", weight_per_unit=275),
            ],
        )

    assert _rows(hoodie) == [("S", 1, True), ("M", 2, True)]
