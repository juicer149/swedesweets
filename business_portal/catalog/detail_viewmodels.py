from __future__ import annotations

from dataclasses import dataclass, replace

from django.urls import reverse

from business_portal.catalog.viewmodels import (
    _build_business_product_card,
    build_business_offer_viewmodel,
)
from common.catalog.contracts import (
    CatalogProduct,
)
from common.catalog.viewmodels import (
    CatalogOfferVM,
    ProductCardVM,
    build_product_tabs,
)
from common.page_tabs import PageTab
from products.images import product_display_url
from products.localization import (
    catalog_text,
)
from products.models import (
    ProductProfile,
)


@dataclass(frozen=True, slots=True)
class BusinessCatalogProductDetailContext:
    catalog_product: CatalogProduct
    product_name: str
    image_url: str | None
    description: str
    ingredients: str
    offers: tuple[
        CatalogOfferVM,
        ...,
    ]
    initial_offer: CatalogOfferVM
    page_tabs: tuple[PageTab, ...]
    title: str
    cancel_url: str
    # The catalog card's parts, for the page's label: sizes, deals, the
    # price tag, the weight, the in-cart badge.
    card: ProductCardVM | None = None

    def as_dict(
        self,
    ) -> dict[str, object]:
        return {
            "catalog_product": (
                self.catalog_product
            ),
            "product": (
                self.catalog_product
                .product
            ),
            "product_name": (
                self.product_name
            ),
            "image_url": (
                self.image_url
            ),
            "description": (
                self.description
            ),
            "ingredients": (
                self.ingredients
            ),
            "offers": self.offers,
            "initial_offer": (
                self.initial_offer
            ),
            "page_tabs": self.page_tabs,
            "title": self.title,
            "cancel_url": (
                self.cancel_url
            ),
            "card": self.card,
        }


def build_business_catalog_product_detail_context(
    *,
    catalog_product: CatalogProduct,
    language_code: str,
    in_cart_units: int = 0,
) -> BusinessCatalogProductDetailContext:
    product = (
        catalog_product.product
    )

    text = catalog_text(
        product,
        language_code=language_code,
    )
    product_name = text.name

    profile = (
        _get_product_profile(
            product=product,
        )
    )

    offers = tuple(
        build_business_offer_viewmodel(
            offer
        )
        for offer
        in catalog_product.offers
    )

    if not offers:
        raise ValueError(
            (
                "Business catalog product "
                "must have at least one offer"
            )
        )

    description = text.description
    ingredients = text.ingredients

    return (
        BusinessCatalogProductDetailContext(
            catalog_product=(
                catalog_product
            ),
            product_name=(
                product_name
            ),
            image_url=(
                _image_url(
                    profile=profile,
                )
            ),
            description=description,
            ingredients=ingredients,
            offers=offers,
            initial_offer=offers[0],
            page_tabs=build_product_tabs(
                description=description,
                ingredients=ingredients,
            ),
            title=product_name,
            cancel_url=reverse(
                "business_portal:catalog"
            ),
            card=replace(
                _build_business_product_card(
                    catalog_product=catalog_product,
                    language_code=language_code,
                ),
                in_cart_units=in_cart_units,
            ),
        )
    )


def _get_product_profile(
    *,
    product,
) -> ProductProfile | None:
    return getattr(
        product,
        "profile",
        None,
    )


def _image_url(
    *,
    profile: ProductProfile | None,
) -> str | None:
    return product_display_url(profile)

