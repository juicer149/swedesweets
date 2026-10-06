from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from business_portal.orders.presentation import (
    contents_summary,
    quantity_label,
)
from business_portal.orders.product_presentation import (
    business_cart_line_presentation,
)
from carts.models import (
    Cart,
    CartLine,
)
from common.lines import META_OFFER, LineView, meta, metas
from products.images import product_image_url


@dataclass(frozen=True, slots=True)
class PortalOrderReviewLine:
    quantity: int
    quantity_label: str
    catalog_label: str
    image_url: str | None
    offer_label: str | None
    price_label: str | None

    @property
    def view(self) -> LineView:
        return LineView(
            name=self.catalog_label,
            image_url=self.image_url,
            metas=metas(
                meta(self.offer_label, META_OFFER),
                meta(self.price_label),
            ),
            # "× 3": the count alone reads cleaner than "3 units".
            aside=f"× {self.quantity}",
        )


@dataclass(frozen=True, slots=True)
class PortalOrderReviewContext:
    lines: tuple[PortalOrderReviewLine, ...]
    title: str
    items_summary: str
    place_order_label: str
    back_label: str
    clear_cart_label: str
    back_url: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "lines": self.lines,
            "title": self.title,
            "items_summary": self.items_summary,
            "place_order_label": self.place_order_label,
            "back_label": self.back_label,
            "clear_cart_label": self.clear_cart_label,
            "back_url": self.back_url,
        }


def build_portal_order_review_context(
    *,
    cart: Cart,
    language_code: str,
) -> PortalOrderReviewContext:
    cart_lines = tuple(
        cart.lines
        .select_related(
            "commercial_price",
            "commercial_price__product",
            "commercial_price__product__profile",
        )
        .prefetch_related(
            "commercial_price__amounts",
            "commercial_price__product__translations",
        )
        .order_by("id")
    )

    lines = tuple(
        _build_review_line(
            line,
            language_code=language_code,
        )
        for line in cart_lines
    )

    return PortalOrderReviewContext(
        lines=lines,
        title=_("Review order"),
        items_summary=contents_summary(
            product_count=len(lines),
            total_quantity=sum(
                line.quantity
                for line in lines
            ),
        ),
        place_order_label=_("Place order"),
        back_label=_("Back"),
        clear_cart_label=_("Clear cart"),
        back_url=reverse(
            "business_portal:cart"
        ),
    )


def _build_review_line(
    line: CartLine,
    *,
    language_code: str,
) -> PortalOrderReviewLine:
    presentation = (
        business_cart_line_presentation(
            line,
            language_code=language_code,
        )
    )

    return PortalOrderReviewLine(
        quantity=line.quantity,
        quantity_label=quantity_label(
            line.quantity
        ),
        catalog_label=(
            presentation.catalog_label
        ),
        image_url=product_image_url(
            line.commercial_price.product,
        ),
        offer_label=(
            presentation.offer_label
        ),
        price_label=(
            presentation.price_label
        ),
    )
