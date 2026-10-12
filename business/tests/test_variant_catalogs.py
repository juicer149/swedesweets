"""Catalogs, carts and orders by variant: a standard offer per variant with
its own stock, its label on the choice, the cart line and the order line;
a paused variant is not sold."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.utils import timezone

from business.drafts import resolve_standard_business_offer
from business.selectors import list_business_catalog_products
from business_portal.catalog.viewmodels import build_business_offer_viewmodel
from business_portal.orders.product_presentation import (
    business_variant_catalog_label,
)
from common.catalog.contracts import CatalogOfferKind
from common.catalog.viewmodels import ProductCardVM, offer_choice_label
from common.ui import UiText
from inventory.tests.factories import batch_factory
from orders.errors import InvalidOrderOperation
from pricing.models import CommercialPrice, PriceAmount
from products.services import set_variant_active
from products.tests.factories import product_factory, variant_factory
from retail.catalog_selectors import list_retail_catalog_products
from storefront.catalog.viewmodels import build_retail_offer_viewmodel

TODAY = timezone.localdate()
BUSINESS = CommercialPrice.Channel.BUSINESS
RETAIL = CommercialPrice.Channel.RETAIL


def _offer(*, variant, channel, price, enabled=True, batch=None, reason=""):
    offer = CommercialPrice.objects.create(
        variant=variant,
        batch=batch,
        channel=channel,
        enabled=enabled,
        reason=reason,
    )
    PriceAmount.objects.create(
        commercial_price=offer,
        currency=PriceAmount.Currency.EUR,
        price=Decimal(price),
    )

    return offer


def _hoodie(channel):
    product = product_factory(name="Hoodie", weight_per_unit=400)
    medium = variant_factory(
        product=product,
        label="M",
        first_label="S",
        weight_per_unit=450,
    )
    small = product.variants.get(label="S")
    batch_factory(product=product, variant=small, today=TODAY, quantity=5)
    batch_factory(
        product=product,
        variant=medium,
        today=TODAY,
        quantity=3,
        batch_id="M-1",
    )
    small_offer = _offer(variant=small, channel=channel, price="2.50")
    medium_offer = _offer(variant=medium, channel=channel, price="4.50")

    return product, small, medium, small_offer, medium_offer


@pytest.mark.django_db
def test_the_business_catalog_has_a_standard_offer_per_variant():
    product, small, medium, small_offer, medium_offer = _hoodie(BUSINESS)

    (catalog_product,) = list_business_catalog_products()

    assert [
        (offer.commercial_price_id, offer.variant_label, offer.available_units)
        for offer in catalog_product.offers
    ] == [
        (small_offer.pk, "S", 5),
        (medium_offer.pk, "M", 3),
    ]
    assert {offer.kind for offer in catalog_product.offers} == {
        CatalogOfferKind.STANDARD,
    }


@pytest.mark.django_db
def test_a_variants_batch_offer_takes_its_stock_from_that_variant():
    product, small, medium, small_offer, medium_offer = _hoodie(BUSINESS)
    short = batch_factory(
        product=product,
        variant=medium,
        today=TODAY,
        quantity=2,
        batch_id="M-SHORT",
    )
    _offer(
        variant=medium,
        batch=short,
        channel=BUSINESS,
        price="3.00",
        reason=CommercialPrice.Reason.SHORT_DATED,
    )

    (catalog_product,) = list_business_catalog_products()
    units = {
        (offer.kind, offer.variant_label): offer.available_units
        for offer in catalog_product.offers
    }

    assert units == {
        (CatalogOfferKind.STANDARD, "S"): 5,
        (CatalogOfferKind.STANDARD, "M"): 3,
        (CatalogOfferKind.BATCH, "M"): 2,
    }


@pytest.mark.django_db
def test_a_paused_variant_is_left_out_of_both_catalogs():
    product, small, medium, *_ = _hoodie(BUSINESS)
    _offer(variant=small, channel=RETAIL, price="2.90")
    _offer(variant=medium, channel=RETAIL, price="4.90")

    set_variant_active(variant=medium, active=False)

    (business_product,) = list_business_catalog_products()
    (retail_product,) = list_retail_catalog_products()

    assert [offer.variant_label for offer in business_product.offers] == ["S"]
    assert [offer.variant_label for offer in retail_product.offers] == ["S"]


@pytest.mark.django_db
def test_the_retail_catalog_lists_the_variants_in_order():
    product, small, medium, small_offer, medium_offer = _hoodie(RETAIL)
    medium.position = 0
    medium.save(update_fields=["position"])

    (catalog_product,) = list_retail_catalog_products()

    assert [
        (offer.variant_label, offer.price, offer.available_units)
        for offer in catalog_product.offers
    ] == [
        ("M", Decimal("4.50"), 3),
        ("S", Decimal("2.50"), 5),
    ]


@pytest.mark.django_db
def test_an_offer_choice_says_its_size():
    product, *_ = _hoodie(RETAIL)
    (catalog_product,) = list_retail_catalog_products()

    labels = [
        build_retail_offer_viewmodel(offer).label
        for offer in catalog_product.offers
    ]

    assert labels == ["S", "M"]
    assert offer_choice_label(variant_label="") == "Standard"
    assert offer_choice_label(variant_label="M", offer_label="Short dated") == (
        "M · Short dated"
    )


@pytest.mark.django_db
def test_a_card_with_several_sizes_leads_to_its_page():
    _hoodie(BUSINESS)
    (catalog_product,) = list_business_catalog_products()
    offers = tuple(
        build_business_offer_viewmodel(offer)
        for offer in catalog_product.offers
    )

    card = ProductCardVM(
        product_id=catalog_product.product.pk,
        name="Hoodie",
        package_label="",
        badge_label=None,
        primary_action=UiText(text="Add", href="#"),
        offers=offers,
    )

    assert card.has_variant_choice is True
    assert ProductCardVM(
        product_id=1,
        name="Apple",
        package_label="",
        badge_label=None,
        primary_action=UiText(text="Add", href="#"),
        offers=offers[:1],
    ).has_variant_choice is False


@pytest.mark.django_db
def test_a_cart_line_names_its_variant_with_its_weight():
    product, small, medium, *_ = _hoodie(BUSINESS)
    only = product_factory(brand="Rambo", name="Twist", weight_per_unit=2000)

    assert business_variant_catalog_label(
        medium,
        product=product,
        language_code="en",
    ) == f"{product.display_name} — M · 450 g"
    assert business_variant_catalog_label(
        only.variants.get(),
        product=only,
        language_code="en",
    ) == "Rambo — Twist · 2000 g"


@pytest.mark.django_db
def test_ordering_by_product_takes_the_first_sold_variant():
    product, small, medium, small_offer, medium_offer = _hoodie(BUSINESS)

    assert resolve_standard_business_offer(product=product) == small_offer

    small_offer.enabled = False
    small_offer.save(update_fields=["enabled"])

    assert resolve_standard_business_offer(product=product) == medium_offer

    medium_offer.enabled = False
    medium_offer.save(update_fields=["enabled"])

    with pytest.raises(InvalidOrderOperation, match="not available"):
        resolve_standard_business_offer(product=product)
