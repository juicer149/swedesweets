"""Prices per variant: a standard offer per variant and channel, set from
the ops form for every variant at once (update_variants_pricing)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.utils import timezone

from inventory.tests.factories import batch_factory
from pricing.errors import InvalidCommercialPrice
from pricing.models import CommercialPrice, PriceAmount
from pricing.product_configuration import (
    VariantPrices,
    VariantPricing,
    update_product_standard_pricing,
    update_variants_pricing,
)
from pricing.selectors import (
    get_variant_commercial_price,
    list_orderable_batches_for_offer,
    standard_prices_by_variant_id,
)
from pricing.services import create_commercial_price, ensure_standard_offer
from pricing.tests.factories import price_amount_factory, pricing_product_factory
from products.services import set_variant_active
from products.tests.factories import variant_factory
from retail.selectors import list_batches_for_retail_price

TODAY = timezone.localdate()
BUSINESS = CommercialPrice.Channel.BUSINESS
RETAIL = CommercialPrice.Channel.RETAIL


def _hoodie():
    product = pricing_product_factory(name="Hoodie")
    medium = variant_factory(product=product, label="M", first_label="S")
    small = product.variants.get(label="S")

    return product, small, medium


def _amount(offer, currency=PriceAmount.Currency.EUR):
    return offer.amounts.get(currency=currency).price


@pytest.mark.django_db
def test_each_variant_has_its_own_standard_offer_per_channel():
    product, small, medium = _hoodie()

    small_offer = ensure_standard_offer(variant=small, channel=BUSINESS)
    medium_offer = ensure_standard_offer(variant=medium, channel=BUSINESS)

    assert small_offer != medium_offer
    assert ensure_standard_offer(variant=medium, channel=BUSINESS) == medium_offer
    assert standard_prices_by_variant_id(product=product, channel=BUSINESS) == {
        small.pk: small_offer,
        medium.pk: medium_offer,
    }


@pytest.mark.django_db
def test_create_commercial_price_for_a_chosen_variant():
    product, _small, medium = _hoodie()

    offer = create_commercial_price(
        product=product,
        variant=medium,
        channel=RETAIL,
    )

    assert offer.variant == medium
    assert get_variant_commercial_price(variant=medium, channel=RETAIL) == offer

    with pytest.raises(InvalidCommercialPrice, match="already exists"):
        create_commercial_price(product=product, variant=medium, channel=RETAIL)


@pytest.mark.django_db
def test_a_product_wide_call_on_several_variants_must_choose_one():
    product, _small, _medium = _hoodie()

    with pytest.raises(InvalidCommercialPrice, match="choose which variant"):
        create_commercial_price(product=product, channel=RETAIL)

    with pytest.raises(InvalidCommercialPrice, match="choose which variant"):
        ensure_standard_offer(product=product, channel=BUSINESS)


def _both_channels(**amounts) -> VariantPricing:
    return VariantPricing(
        retail_enabled=True,
        business_enabled=True,
        prices=VariantPrices(**amounts),
    )


@pytest.mark.django_db
def test_update_variants_pricing_sets_each_variants_amounts():
    product, small, medium = _hoodie()

    update_variants_pricing(
        product=product,
        pricing={
            small.pk: _both_channels(
                business_eur=Decimal("1.90"),
                retail_eur=Decimal("2.50"),
            ),
            medium.pk: _both_channels(
                business_eur=Decimal("3.40"),
                retail_eur=Decimal("4.50"),
                retail_sek=Decimal("49.00"),
            ),
        },
    )

    business = standard_prices_by_variant_id(product=product, channel=BUSINESS)
    retail = standard_prices_by_variant_id(product=product, channel=RETAIL)

    assert _amount(business[small.pk]) == Decimal("1.90")
    assert _amount(business[medium.pk]) == Decimal("3.40")
    assert _amount(retail[small.pk]) == Decimal("2.50")
    assert _amount(retail[medium.pk]) == Decimal("4.50")
    assert _amount(retail[medium.pk], PriceAmount.Currency.SEK) == Decimal("49.00")
    assert all(offer.enabled for offer in [*business.values(), *retail.values()])


@pytest.mark.django_db
def test_a_variant_left_out_keeps_its_amounts():
    product, small, medium = _hoodie()
    update_variants_pricing(
        product=product,
        pricing={
            small.pk: _both_channels(
                business_eur=Decimal("1.90"),
                retail_eur=Decimal("2.50"),
            ),
            medium.pk: _both_channels(
                business_eur=Decimal("3.40"),
                retail_eur=Decimal("4.50"),
            ),
        },
    )

    update_variants_pricing(
        product=product,
        pricing={
            small.pk: _both_channels(
                business_eur=Decimal("2.00"),
                retail_eur=Decimal("2.50"),
            ),
        },
    )

    business = standard_prices_by_variant_id(product=product, channel=BUSINESS)
    assert _amount(business[small.pk]) == Decimal("2.00")
    assert _amount(business[medium.pk]) == Decimal("3.40")


@pytest.mark.django_db
def test_standard_pricing_gives_every_variant_the_same():
    product, small, medium = _hoodie()

    update_product_standard_pricing(
        product=product,
        business_eur=Decimal("1.90"),
        business_sek=None,
        business_enabled=True,
        retail_eur=Decimal("2.50"),
        retail_sek=None,
        retail_enabled=False,
    )

    business = standard_prices_by_variant_id(product=product, channel=BUSINESS)
    retail = standard_prices_by_variant_id(product=product, channel=RETAIL)

    assert {_amount(business[pk]) for pk in (small.pk, medium.pk)} == {
        Decimal("1.90"),
    }
    assert not any(offer.enabled for offer in retail.values())


@pytest.mark.django_db
def test_prices_for_another_products_variant_are_refused():
    product, _small, _medium = _hoodie()
    other = pricing_product_factory(name="Cap")

    with pytest.raises(InvalidCommercialPrice, match="another product"):
        update_variants_pricing(
            product=product,
            pricing={other.variants.get().pk: _both_channels()},
        )


@pytest.mark.django_db
def test_a_variants_retail_offer_sells_its_own_stock_at_its_own_price():
    product, small, medium = _hoodie()
    small_batch = batch_factory(product=product, variant=small, today=TODAY)
    medium_batch = batch_factory(
        product=product,
        variant=medium,
        today=TODAY,
        batch_id="M-1",
    )
    small_offer = CommercialPrice.objects.create(
        variant=small, channel=RETAIL, enabled=True,
    )
    medium_offer = CommercialPrice.objects.create(
        variant=medium, channel=RETAIL, enabled=True,
    )
    price_amount_factory(commercial_price=small_offer, price=Decimal("2.50"))
    price_amount_factory(commercial_price=medium_offer, price=Decimal("4.50"))

    assert list(
        list_batches_for_retail_price(
            commercial_price=medium_offer,
            currency=PriceAmount.Currency.EUR,
            today=TODAY,
        )
    ) == [medium_batch]
    assert list(
        list_batches_for_retail_price(
            commercial_price=small_offer,
            currency=PriceAmount.Currency.EUR,
            today=TODAY,
        )
    ) == [small_batch]


@pytest.mark.django_db
def test_a_paused_variant_has_nothing_to_sell():
    product, small, medium = _hoodie()
    batch_factory(product=product, variant=medium, today=TODAY, batch_id="M-1")
    offer = CommercialPrice.objects.create(
        variant=medium, channel=RETAIL, enabled=True,
    )

    set_variant_active(variant=medium, active=False)
    offer.refresh_from_db()

    assert not list_orderable_batches_for_offer(
        offer=offer,
        currency=PriceAmount.Currency.EUR,
        today=TODAY,
    ).exists()


@pytest.mark.django_db
def test_a_variant_whose_prices_nothing_used_can_still_be_deleted():
    from products.services import delete_variant, variant_has_history

    product, _small, medium = _hoodie()
    offer = ensure_standard_offer(variant=medium, channel=BUSINESS)
    price_amount_factory(commercial_price=offer, price=Decimal("3.40"))

    assert variant_has_history(medium) is False

    delete_variant(variant=medium)

    assert not CommercialPrice.objects.filter(pk=offer.pk).exists()
    assert list(product.variants.values_list("label", flat=True)) == ["S"]


@pytest.mark.django_db
def test_a_variant_in_a_cart_is_history():
    from carts.models import Cart, CartLine
    from common.channels import SalesChannel
    from products.services import variant_has_history

    _product, _small, medium = _hoodie()
    offer = ensure_standard_offer(variant=medium, channel=BUSINESS)
    cart = Cart.objects.create(channel=SalesChannel.BUSINESS)
    CartLine.objects.create(cart=cart, commercial_price=offer, quantity=1)

    assert variant_has_history(medium) is True


@pytest.mark.django_db
def test_each_variant_has_its_own_sales_channels():
    product, small, medium = _hoodie()

    update_variants_pricing(
        product=product,
        pricing={
            small.pk: VariantPricing(
                retail_enabled=True,
                business_enabled=False,
                prices=VariantPrices(retail_eur=Decimal("2.50")),
            ),
            medium.pk: VariantPricing(
                retail_enabled=False,
                business_enabled=True,
                prices=VariantPrices(business_eur=Decimal("3.40")),
            ),
        },
    )

    retail = standard_prices_by_variant_id(product=product, channel=RETAIL)
    business = standard_prices_by_variant_id(product=product, channel=BUSINESS)

    assert retail[small.pk].enabled is True
    assert medium.pk not in retail
    assert business[small.pk].enabled is False
    assert business[medium.pk].enabled is True


@pytest.mark.django_db
def test_a_variant_sold_in_retail_needs_a_price():
    product, small, _medium = _hoodie()

    with pytest.raises(InvalidCommercialPrice, match="give it a retail price"):
        update_variants_pricing(
            product=product,
            pricing={
                small.pk: VariantPricing(
                    retail_enabled=True,
                    business_enabled=True,
                    prices=VariantPrices(),
                ),
            },
        )
