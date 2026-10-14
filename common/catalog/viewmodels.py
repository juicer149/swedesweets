from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.utils.translation import gettext_lazy as _

from common.page_tabs import PageTab
from common.ui import UiText


def catalog_price_label(price: Decimal) -> str:
    """A catalog price: "€50" when it is whole, "€12.50" otherwise (carts,
    checkout and mails keep their cents)."""

    if price == price.to_integral_value():
        return f"€{price:.0f}"

    return f"€{price:.2f}"


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
    # For the card: the cheapest size's price on its tag, the sizes in
    # their order.
    price: Decimal | None = None
    position: int = 0

    @property
    def sold_out(self) -> bool:
        return self.available_units <= 0

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
class PriceTagVM:
    """The tag hung on a card's picture: its price, and a special offer's
    reason ("Short dated") when there is one."""

    price_label: str
    deal_label: str | None = None


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
    # Sizes on sale with nothing to sell now: in the size list, muted.
    sold_out: tuple[CatalogOfferVM, ...] = ()
    # How many the visitor's cart holds (all sizes): a badge on the picture.
    in_cart_units: int = 0
    # The card's own: just the weight ("4000 g"), no stock unit.
    weight_label: str = ""

    @property
    def initial_offer(self) -> CatalogOfferVM | None:
        """The offer the tile adds when it has no sizes to choose from
        (the first, normally standard)."""

        return self.offers[0] if self.offers else None

    @property
    def size_choices(self) -> tuple[CatalogOfferVM, ...]:
        """The sizes, in their order: each variant's standard offer, the
        sold-out ones too (muted, not choosable)."""

        return tuple(
            sorted(
                (
                    *(offer for offer in self.offers if offer.kind == "standard"),
                    *self.sold_out,
                ),
                key=lambda offer: offer.position,
            )
        )

    @property
    def has_size_choice(self) -> bool:
        """Several sizes: the tile's left half is a size dropdown (and the
        cart button waits for a size); otherwise it shows the package."""

        choices = self.size_choices

        return len(choices) > 1 and any(not offer.sold_out for offer in choices)

    @property
    def price_tag(self) -> PriceTagVM | None:
        """The price tag on the picture's corner, when there is a price:
        the cheapest size's, "from" when the sizes differ; a special
        offer's reason above it."""

        deal = self.initial_offer.badge_label if self.initial_offer else None
        deal = deal or (self.other_deal.badge_label if self.other_deal else None)

        if not self.has_size_choice:
            offer = self.initial_offer
            if offer is None or not offer.price_label:
                return None

            return PriceTagVM(price_label=offer.price_label, deal_label=deal)

        priced = [
            offer
            for offer in self.size_choices
            if not offer.sold_out and offer.price is not None and offer.price_label
        ]

        if not priced:
            return None

        cheapest = min(priced, key=lambda offer: offer.price)
        prices = {offer.price for offer in priced}

        return PriceTagVM(
            price_label=(
                str(_("from %(price)s") % {"price": cheapest.price_label})
                if len(prices) > 1
                else cheapest.price_label
            ),
            deal_label=deal,
        )

    @property
    def size_rows(
        self,
    ) -> tuple[tuple[CatalogOfferVM, CatalogOfferVM | None], ...]:
        """Each size with its special offer, if it has one (a product's
        page shows it once the size is chosen)."""

        return tuple(
            (choice, self._deal_at(choice.position))
            for choice in self.size_choices
        )

    @property
    def only_deal(self) -> CatalogOfferVM | None:
        """A one-size product's special offer beside its standard one."""

        offer = self.initial_offer

        if self.has_size_choice or offer is None or offer.kind != "standard":
            return None

        return self._deal_at(offer.position)

    def _deal_at(self, position: int) -> CatalogOfferVM | None:
        return next(
            (
                offer
                for offer in self.offers
                if offer.kind != "standard" and offer.position == position
            ),
            None,
        )

    @property
    def other_deal(self) -> CatalogOfferVM | None:
        """A special offer besides the one the tile adds: a hint on the
        tile that the product page has another choice."""

        return next(
            (offer for offer in self.offers[1:] if offer.badge_label),
            None,
        )


def offer_choice_label(
    *,
    variant_label: str,
    offer_label: str | None = None,
) -> str:
    """What an offer's choice says: the variant's label ("M"), then a batch
    offer's reason ("M · Short dated"); a product's only variant has no
    label, so its standard offer is "Standard"."""

    if offer_label is None:
        return variant_label or str(_("Standard"))

    if variant_label:
        return f"{variant_label} · {offer_label}"

    return offer_label


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
