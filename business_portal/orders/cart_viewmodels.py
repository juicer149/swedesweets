from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from business_portal.orders.product_presentation import (
    business_cart_line_presentation,
)
from carts.models import Cart


@dataclass(frozen=True, slots=True)
class PortalCartLine:
    cart_line_id: int
    product_label: str
    offer_label: str | None
    price_label: str | None
    quantity: int
    quantity_url: str
    remove_url: str


@dataclass(frozen=True, slots=True)
class PortalCartContext:
    cart_lines: tuple[PortalCartLine, ...]
    title: str
    description: str
    submit_label: str
    clear_cart_label: str
    continue_shopping_label: str
    continue_shopping_url: str
    cancel_url: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "cart_lines": self.cart_lines,
            "title": self.title,
            "description": self.description,
            "submit_label": self.submit_label,
            "clear_cart_label": self.clear_cart_label,
            "continue_shopping_label": self.continue_shopping_label,
            "continue_shopping_url": self.continue_shopping_url,
            "cancel_url": self.cancel_url,
        }


def build_portal_cart_context(
    *,
    cart: Cart | None,
    language_code: str | None = None,
) -> PortalCartContext:
    cart_lines = (
        _build_portal_cart_lines(
            cart=cart,
            language_code=language_code,
        )
        if cart is not None
        else ()
    )

    return PortalCartContext(
        cart_lines=cart_lines,
        title=_("Cart"),
        description=_(
            "Review the products and quantities in your cart."
        ),
        submit_label=_("Review order"),
        clear_cart_label=_("Clear cart"),
        continue_shopping_label=_("Continue shopping"),
        continue_shopping_url=reverse(
            "business_portal:catalog"
        ),
        cancel_url=reverse(
            "accounts:after_login"
        ),
    )


def _build_portal_cart_lines(
    *,
    cart: Cart,
    language_code: str | None,
) -> tuple[PortalCartLine, ...]:
    lines = (
        cart.lines
        .select_related(
            "commercial_price",
            "commercial_price__product",
        )
        .prefetch_related(
            "commercial_price__amounts",
            "commercial_price__product__translations",
        )
        .order_by("id")
    )

    effective_language_code = (
        language_code or "en"
    )

    cart_lines = []

    for line in lines:
        presentation = (
            business_cart_line_presentation(
                line,
                language_code=effective_language_code,
            )
        )

        cart_lines.append(
            PortalCartLine(
                cart_line_id=line.id,
                product_label=(
                    presentation.catalog_label
                ),
                offer_label=(
                    presentation.offer_label
                ),
                price_label=(
                    presentation.price_label
                ),
                quantity=line.quantity,
                quantity_url=reverse(
                    "business_portal:set_cart_line_quantity",
                    kwargs={
                        "cart_line_id": line.id,
                    },
                ),
                remove_url=reverse(
                    "business_portal:remove_cart_line",
                    kwargs={
                        "cart_line_id": line.id,
                    },
                ),
            )
        )

    return tuple(
        cart_lines
    )
