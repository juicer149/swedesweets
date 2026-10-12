"""The product's Catalog tab: the shop's product page, once per language.

Each preview is the page the shop shows (includes/catalog/product.html) in
that language, with its fallbacks (products/localization.py): the name,
category, picture, price and stock, and Description and Ingredients. Shown,
not used: its form is inert.

The offers are the shop's own (retail.catalog_selectors); a product that is
not in the shop now (inactive, no retail price, nothing in stock) is shown
without a price. The labels mirror storefront/catalog/viewmodels.py (the
same words, so the same translations): a small duplication rather than ops
importing the shop's presentation.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.utils import translation
from django.utils.translation import gettext, ngettext

from common.catalog.contracts import (
    CatalogOffer,
    CatalogOfferKind,
    CatalogProduct,
)
from common.catalog.viewmodels import (
    CatalogOfferVM,
    build_product_tabs,
    offer_choice_label,
)
from common.page_tabs import PageTab
from pricing.models import CommercialPrice
from products.images import product_display_url
from products.localization import catalog_languages, catalog_text
from products.models import Product

# Under this many, the shop says how few are left.
FEW_LEFT = 10


@dataclass(frozen=True, slots=True)
class CatalogPagePreview:
    language_code: str
    language_name: str
    product_name: str
    category_label: str | None
    image_url: str | None
    description: str
    ingredients: str
    offers: tuple[CatalogOfferVM, ...]
    initial_offer: CatalogOfferVM | None
    page_tabs: tuple[PageTab, ...]

    @property
    def id_prefix(self) -> str:
        return f"preview-{self.language_code}-"


def build_catalog_page_previews(
    *,
    product: Product,
    shop_product: CatalogProduct | None,
) -> tuple[CatalogPagePreview, ...]:
    """One preview per catalog language, the first language first."""

    return tuple(
        _build_preview(
            product=product,
            shop_product=shop_product,
            language_code=code,
            language_name=name,
        )
        for code, name in catalog_languages()
    )


def _build_preview(
    *,
    product: Product,
    shop_product: CatalogProduct | None,
    language_code: str,
    language_name: str,
) -> CatalogPagePreview:
    text = catalog_text(product, language_code=language_code)
    profile = getattr(product, "profile", None)

    with translation.override(language_code):
        offers = tuple(
            _offer(offer)
            for offer in (shop_product.offers if shop_product else ())
        )
        category_label = (
            str(profile.get_category_display())
            if profile is not None and profile.category
            else None
        )

    return CatalogPagePreview(
        language_code=language_code,
        language_name=language_name,
        product_name=text.name,
        category_label=category_label,
        image_url=product_display_url(profile),
        description=text.description,
        ingredients=text.ingredients,
        offers=offers,
        initial_offer=offers[0] if offers else None,
        page_tabs=build_product_tabs(
            description=text.description,
            ingredients=text.ingredients,
        ),
    )


def _offer(offer: CatalogOffer) -> CatalogOfferVM:
    reason_label = _reason_label(offer.reason)
    is_standard = offer.kind == CatalogOfferKind.STANDARD

    return CatalogOfferVM(
        commercial_price_id=offer.commercial_price_id,
        batch_id=offer.batch_id,
        kind=offer.kind.value,
        label=offer_choice_label(
            variant_label=offer.variant_label,
            offer_label=None if is_standard else reason_label,
        ),
        badge_label=(
            (reason_label if offer.reason else None)
            if is_standard
            else reason_label
        ),
        price_label=(
            f"€{offer.price:.2f}" if offer.price is not None else None
        ),
        availability_label=_availability_label(offer.available_units),
        available_units=offer.available_units,
    )


def _reason_label(reason: str | None) -> str:
    if not reason:
        return gettext("Special offer")

    try:
        return str(CommercialPrice.Reason(reason).label)
    except ValueError:
        return gettext("Special offer")


def _availability_label(available_units: int) -> str:
    if available_units < FEW_LEFT:
        return ngettext(
            "Only %(count)s left",
            "Only %(count)s left",
            available_units,
        ) % {"count": available_units}

    return gettext("In stock")
