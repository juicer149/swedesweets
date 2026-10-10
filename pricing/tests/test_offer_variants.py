from __future__ import annotations

import pytest

from pricing.errors import InvalidCommercialPrice
from pricing.models import CommercialPrice
from pricing.services import ensure_standard_offer
from pricing.tests.factories import (
    commercial_price_factory,
    pricing_batch_factory,
    pricing_product_factory,
)
from products.tests.factories import variant_factory


@pytest.mark.django_db
def test_a_standard_offer_is_for_the_product_only_variant():
    product = pricing_product_factory()

    offer = ensure_standard_offer(
        product=product,
        channel=CommercialPrice.Channel.BUSINESS,
    )

    assert offer.variant == product.variants.get()


@pytest.mark.django_db
def test_a_batch_offer_is_for_the_batch_variant():
    product = pricing_product_factory()
    batch = pricing_batch_factory(product=product)

    offer = commercial_price_factory(batch=batch)

    assert offer.variant == batch.variant
    assert offer.product == product


@pytest.mark.django_db
def test_an_offer_can_be_for_a_chosen_variant():
    product = pricing_product_factory(name="Hoodie")
    medium = variant_factory(product=product, label="M")

    offer = CommercialPrice.objects.create(
        variant=medium,
        channel=CommercialPrice.Channel.RETAIL,
    )

    assert offer.product == product
    assert offer.variant == medium


@pytest.mark.django_db
def test_a_product_with_several_variants_needs_one_chosen():
    product = pricing_product_factory(name="Hoodie")
    variant_factory(product=product, label="M")

    with pytest.raises(InvalidCommercialPrice, match="choose which variant"):
        CommercialPrice.objects.create(
            product=product,
            channel=CommercialPrice.Channel.RETAIL,
        )


@pytest.mark.django_db
def test_a_batch_offer_cannot_be_for_another_variant():
    product = pricing_product_factory(name="Hoodie")
    batch = pricing_batch_factory(product=product)
    medium = variant_factory(product=product, label="M")

    with pytest.raises(InvalidCommercialPrice, match="batch's own variant"):
        CommercialPrice.objects.create(
            product=product,
            variant=medium,
            batch=batch,
            channel=CommercialPrice.Channel.RETAIL,
        )


@pytest.mark.django_db
def test_an_offer_cannot_be_for_another_product_variant():
    apple = pricing_product_factory(name="Apple")
    pear = pricing_product_factory(name="Pear")

    with pytest.raises(InvalidCommercialPrice, match="another product"):
        CommercialPrice.objects.create(
            product=apple,
            variant=pear.variants.get(),
            channel=CommercialPrice.Channel.RETAIL,
        )
