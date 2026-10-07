from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from common.page_tabs import PageTab
from common.ui import UiText


@dataclass(frozen=True, slots=True)
class CatalogOfferVM:
    """Presentation contract for one selectable catalog offer."""

    commercial_price_id: int
    batch_id: int | None
    kind: str
    label: str
    badge_label: str | None
    price_label: str | None
    availability_label: str
    available_units: int

    def as_dict(self) -> dict[str, object]:
        return {
            "commercial_price_id": self.commercial_price_id,
            "batch_id": self.batch_id,
            "kind": self.kind,
            "label": self.label,
            "badge_label": self.badge_label,
            "price_label": self.price_label,
            "availability_label": self.availability_label,
            "available_units": self.available_units,
        }


@dataclass(frozen=True, slots=True)
class ProductCardVM:
    """Presentation contract for one product card in a product list view."""

    product_id: int
    name: str
    package_label: str
    badge_label: str | None
    primary_action: UiText
    image_url: str | None = None
    secondary_action: UiText | None = None
    offers: tuple[CatalogOfferVM, ...] = ()
    category_key: str = "other"
    search_text: str = ""

    @property
    def initial_offer(self) -> CatalogOfferVM | None:
        """The offer the tile's "+" adds (the first, normally standard)."""

        return self.offers[0] if self.offers else None

    @property
    def other_deal(self) -> CatalogOfferVM | None:
        """A special offer besides the one the tile adds: a hint on the
        tile that the product page has another choice."""

        return next(
            (offer for offer in self.offers[1:] if offer.badge_label),
            None,
        )


def build_product_tabs(
    *,
    description: str,
    ingredients: str,
) -> tuple[PageTab, ...]:
    """The tabs under a catalog product: Description and Ingredients, each
    only when the product has it."""

    tabs: list[PageTab] = []

    if description:
        tabs.append(
            PageTab(
                key="description",
                label=_("Description"),
                template="includes/catalog/tab_description.html",
            )
        )

    if ingredients:
        tabs.append(
            PageTab(
                key="ingredients",
                label=_("Ingredients"),
                template="includes/catalog/tab_ingredients.html",
            )
        )

    return tuple(tabs)
