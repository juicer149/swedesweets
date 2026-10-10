from __future__ import annotations

import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from products.catalog import variant_display_name
from products.errors import InvalidProductData
from products.models import ProductVariant
from products.services import create_product
from products.tests.factories import product_factory, variant_factory


@pytest.mark.django_db
def test_a_new_product_has_its_only_variant():
    product = product_factory(
        brand="Fazer",
        name="Tutti Frutti",
        weight_per_unit=2000,
        internal_number=7,
    )

    variant = product.variants.get()

    assert variant.label == ""
    assert variant.position == 1
    assert variant.sku == product.sku == "SS-007"
    assert variant.weight_per_unit == 2000
    assert variant.active is True


@pytest.mark.django_db
def test_an_existing_product_is_not_given_a_second_variant():
    first = create_product(
        brand="Fazer",
        name="Tutti Frutti",
        weight_per_unit=2000,
        internal_number=7,
    )
    again = create_product(
        brand="Fazer",
        name="Tutti Frutti",
        weight_per_unit=2000,
        internal_number=7,
    )

    assert again.created is False
    assert again.item == first.item
    assert ProductVariant.objects.count() == 1


@pytest.mark.django_db
def test_the_only_variant_is_named_as_its_product():
    product = product_factory(
        brand="SwedeSweets",
        name="Hoodie",
    )

    assert product.variants.get().display_name == "SwedeSweets — Hoodie"


@pytest.mark.django_db
def test_a_labelled_variant_adds_its_label_to_the_name():
    product = product_factory(
        brand="SwedeSweets",
        name="Hoodie",
    )

    variant = variant_factory(
        product=product,
        label="M",
    )

    assert variant.display_name == "SwedeSweets — Hoodie — M"
    assert variant.position == 2


def test_the_name_helper_takes_any_product_name():
    assert variant_display_name("Sweat à capuche", "M") == (
        "Sweat à capuche — M"
    )
    assert variant_display_name("Sweat à capuche", "") == "Sweat à capuche"


@pytest.mark.django_db
def test_variants_are_listed_by_position():
    product = product_factory(
        name="Hoodie",
    )
    large = variant_factory(
        product=product,
        label="L",
        position=3,
    )
    small = variant_factory(
        product=product,
        label="S",
        position=2,
    )

    assert list(product.variants.all()) == [
        product.variants.get(label=""),
        small,
        large,
    ]


@pytest.mark.django_db
def test_a_label_is_tidied():
    product = product_factory(
        name="Chocolate",
    )

    variant = variant_factory(
        product=product,
        label="  60   g ",
    )

    assert variant.label == "60 g"


@pytest.mark.django_db
def test_labels_are_unique_within_a_product_whatever_the_case():
    product = product_factory(
        name="Hoodie",
    )
    variant_factory(
        product=product,
        label="XL",
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        ProductVariant.objects.create(
            product=product,
            label="xl",
            position=3,
            sku=f"{product.sku}-XL-2",
            weight_per_unit=product.weight_per_unit,
        )


@pytest.mark.django_db
def test_two_products_may_use_the_same_label():
    hoodie = product_factory(
        name="Hoodie",
    )
    t_shirt = product_factory(
        name="T-shirt",
    )

    variant_factory(product=hoodie, label="M")
    variant_factory(product=t_shirt, label="M")

    assert ProductVariant.objects.filter(label="M").count() == 2


@pytest.mark.django_db
def test_a_variant_keeps_its_sku():
    variant = product_factory().variants.get()
    variant.sku = "SOMETHING-ELSE"

    with pytest.raises(InvalidProductData, match="sku cannot be changed"):
        variant.save()


@pytest.mark.django_db
def test_a_variant_weight_must_be_within_bounds():
    product = product_factory()

    with pytest.raises(InvalidProductData, match="weight_per_unit"):
        ProductVariant.objects.create(
            product=product,
            label="Huge",
            position=2,
            sku=f"{product.sku}-HUGE",
            weight_per_unit=0,
        )


@pytest.mark.django_db
def test_a_product_with_variants_cannot_be_deleted():
    product = product_factory()

    with pytest.raises(ProtectedError), transaction.atomic():
        product.delete()
