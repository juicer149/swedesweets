"""Catalogs, carts and orders by variant: a standard offer per variant with
its own stock, its label on the choice, the cart line and the order line;
a paused variant is not sold; a size on sale with no stock is listed sold
out on the card, which has a size dropdown and the cheapest price."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from business.drafts import resolve_standard_business_offer
from business.selectors import list_business_catalog_products
from business_portal.catalog.viewmodels import build_business_offer_viewmodel
from business_portal.orders.product_presentation import (
    business_variant_catalog_label,
)
from carts.selectors import units_in_cart_by_product_id
from carts.services import add_cart_line, create_cart
from common.catalog.contracts import CatalogOfferKind
from common.catalog.viewmodels import (
    ProductCardVM,
    catalog_price_label,
    offer_choice_label,
)
from common.channels import SalesChannel
from common.ui import UiText
from inventory.tests.factories import batch_factory
from orders.errors import InvalidOrderOperation
from pricing.models import CommercialPrice, PriceAmount
from products.services import set_variant_active
from products.tests.factories import product_factory, variant_factory
from retail.catalog_selectors import list_retail_catalog_products
from storefront.catalog.viewmodels import (
    build_retail_offer_viewmodel,
    build_retail_product_cards,
)

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
    # M before S (positions start at 1).
    small.position = 3
    small.save(update_fields=["position"])

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


def _card(offers, sold_out=()):
    return ProductCardVM(
        product_id=1,
        name="Hoodie",
        package_label="400 g",
        badge_label=None,
        primary_action=UiText(text="Add", href="#"),
        offers=tuple(offers),
        sold_out=tuple(sold_out),
    )


def _with_large(product, channel):
    large = variant_factory(product=product, label="L", weight_per_unit=500)
    # On sale, nothing in stock.
    _offer(variant=large, channel=channel, price="4.50")

    return large


@pytest.mark.django_db
@pytest.mark.parametrize("channel", [BUSINESS, RETAIL])
def test_a_size_on_sale_with_no_stock_is_listed_sold_out(channel):
    product, *_ = _hoodie(channel)
    _with_large(product, channel)
    list_products = (
        list_business_catalog_products
        if channel == BUSINESS
        else list_retail_catalog_products
    )

    (catalog_product,) = list_products()

    assert [offer.variant_label for offer in catalog_product.offers] == ["S", "M"]
    assert [
        (offer.variant_label, offer.available_units)
        for offer in catalog_product.sold_out
    ] == [("L", 0)]


@pytest.mark.django_db
def test_a_paused_size_is_not_listed_sold_out():
    product, *_ = _hoodie(RETAIL)
    large = _with_large(product, RETAIL)
    set_variant_active(variant=large, active=False)

    (catalog_product,) = list_retail_catalog_products()

    assert catalog_product.sold_out == ()


@pytest.mark.django_db
def test_a_card_with_several_sizes_has_a_size_dropdown():
    product, *_ = _hoodie(RETAIL)
    _with_large(product, RETAIL)
    (catalog_product,) = list_retail_catalog_products()
    card = _card(
        (build_retail_offer_viewmodel(offer) for offer in catalog_product.offers),
        (build_retail_offer_viewmodel(offer) for offer in catalog_product.sold_out),
    )

    assert card.has_size_choice is True
    assert [
        (choice.label, choice.sold_out) for choice in card.size_choices
    ] == [("S", False), ("M", False), ("L", True)]
    # The cheapest size's price, "from" as the sizes differ.
    assert card.price_tag.price_label == "from €2.50"
    # Whole prices without cents.
    assert catalog_price_label(Decimal("50.00")) == "€50"
    assert catalog_price_label(Decimal("4.90")) == "€4.90"

    one_size = _card(card.offers[:1])
    assert one_size.has_size_choice is False
    assert one_size.price_tag.price_label == "€2.50"


@pytest.mark.django_db
def test_sizes_at_one_price_need_no_from():
    _hoodie(BUSINESS)
    (catalog_product,) = list_business_catalog_products()
    offers = [
        build_business_offer_viewmodel(offer) for offer in catalog_product.offers
    ]
    same_price = [
        replace(offer, price=Decimal("2.50"), price_label="€2.50")
        for offer in offers
    ]

    assert _card(same_price).price_tag.price_label == "€2.50"
    # Unpriced (a business standard offer may be): no tag.
    unpriced = [replace(offer, price=None, price_label=None) for offer in offers]
    assert _card(unpriced).price_tag is None


@pytest.mark.django_db
def test_a_card_whose_sizes_are_all_sold_out_adds_its_deal():
    # Only a batch offer left: no dropdown of nothing but sold-out sizes.
    product, small, medium, small_offer, medium_offer = _hoodie(RETAIL)
    deal = build_retail_offer_viewmodel(
        list_retail_catalog_products()[0].offers[0]
    )
    deal = replace(deal, kind="batch", badge_label="Short dated")
    sold = [
        replace(build_retail_offer_viewmodel(offer), available_units=0)
        for offer in list_retail_catalog_products()[0].offers
    ]

    card = _card([deal], sold)

    assert card.has_size_choice is False
    assert card.initial_offer == deal
    assert card.price_tag.deal_label == "Short dated"


@pytest.mark.django_db
def test_a_card_counts_what_the_cart_holds_of_its_product():
    product, small, medium, small_offer, medium_offer = _hoodie(RETAIL)
    other = product_factory(name="Apple")
    cart = create_cart(channel=SalesChannel.RETAIL)
    add_cart_line(cart=cart, commercial_price=small_offer, quantity=2)
    add_cart_line(cart=cart, commercial_price=medium_offer, quantity=3)

    in_cart = units_in_cart_by_product_id(cart=cart)

    # Both sizes together.
    assert in_cart == {product.pk: 5}
    assert units_in_cart_by_product_id(cart=None) == {}

    (card,) = build_retail_product_cards(
        products=list_retail_catalog_products(),
        language_code="en",
        in_cart=in_cart,
    )
    assert card.in_cart_units == 5
    assert other.pk not in in_cart


@pytest.mark.django_db
def test_the_shop_catalog_shows_the_size_dropdown(client):
    product, *_ = _hoodie(RETAIL)
    _with_large(product, RETAIL)

    html = client.get(reverse("storefront:product_list")).content.decode()

    assert "data-size-select" in html
    assert "data-in-cart" in html
    assert "L — sold out" in html
    assert "from €2.50" in html
    assert 'name="quantity"' in html


@pytest.mark.django_db
def test_a_card_with_one_size_shows_just_its_weight(client):
    product = product_factory(name="Apple", weight_per_unit=4000)
    _offer(variant=product.variants.get(), channel=RETAIL, price="9.00")
    batch_factory(product=product, today=TODAY, quantity=5)

    html = client.get(reverse("storefront:product_list")).content.decode()

    assert '<span class="tile__package">4000 g</span>' in html


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


@pytest.mark.django_db
def test_the_product_page_chooses_the_size_and_shows_its_offer(client):
    product, small, medium, small_offer, medium_offer = _hoodie(RETAIL)
    _with_large(product, RETAIL)
    short = batch_factory(
        product=product,
        variant=medium,
        today=TODAY,
        quantity=2,
        batch_id="M-SHORT",
    )
    deal = _offer(
        variant=medium,
        batch=short,
        channel=RETAIL,
        price="3.00",
        reason=CommercialPrice.Reason.SHORT_DATED,
    )

    html = client.get(
        reverse("storefront:product_detail", kwargs={"product_id": product.pk})
    ).content.decode()

    assert 'id="product-size"' in html
    assert "L — sold out" in html
    # M carries its special offer, shown once M is chosen.
    assert f'data-deal-id="{deal.pk}"' in html
    assert "data-deal-input" in html
    assert "from €2.50" in html
    assert "product__band" in html
