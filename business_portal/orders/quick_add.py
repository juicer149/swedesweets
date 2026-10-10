"""The quick add at the top of a shop's cart: one search field to put
any product of the catalog in the order without going back to it.

Each option is one offer of the catalog (a product's standard offer, and
its special offers beside it), drawn by the enhanced select like a cart
line: the picture, the name, and under it the package, the price and,
only when few are left, how many (the catalog's rule).
"""

from __future__ import annotations

from dataclasses import dataclass

from business.selectors import list_business_catalog_products
from business_portal.catalog.viewmodels import (
    build_business_product_cards,
    few_left_label,
)


@dataclass(frozen=True, slots=True)
class QuickAddOption:
    commercial_price_id: int
    name: str
    package_label: str
    offer_label: str
    price_label: str
    stock_label: str
    image_url: str

    @property
    def text(self) -> str:
        """The plain option text, for a browser without the script."""

        return " · ".join(
            part
            for part in (
                self.name,
                self.package_label,
                self.offer_label,
                self.price_label,
                self.stock_label,
            )
            if part
        )

    @property
    def search_text(self) -> str:
        return " ".join(
            part
            for part in (
                self.name,
                self.package_label,
                self.offer_label,
            )
            if part
        )


def build_cart_quick_add_options(
    *,
    language_code: str,
) -> tuple[QuickAddOption, ...]:
    cards = build_business_product_cards(
        products=list_business_catalog_products(),
        language_code=language_code,
    )

    return tuple(
        QuickAddOption(
            commercial_price_id=offer.commercial_price_id,
            name=card.name,
            package_label=card.package_label,
            offer_label=offer.badge_label or "",
            price_label=offer.price_label or "",
            stock_label=few_left_label(offer.available_units),
            image_url=card.image_url or "",
        )
        for card in cards
        for offer in card.offers
    )
