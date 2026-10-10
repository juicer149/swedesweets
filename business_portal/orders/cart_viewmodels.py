from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from business_portal.orders.product_presentation import (
    business_cart_line_presentation,
)
from carts.models import Cart
from common.lines import META_OFFER, LineView, meta, metas
from products.images import product_image_url


@dataclass(frozen=True, slots=True)
class PortalCartLine:
    cart_line_id: int
    product_label: str
    product_url: str
    image_url: str | None
    offer_label: str | None
    price_label: str | None
    quantity: int
    quantity_url: str
    remove_url: str

    @property
    def view(self) -> LineView:
        return LineView(
            name=self.product_label,
            href=self.product_url,
            image_url=self.image_url,
            metas=metas(
                meta(self.offer_label, META_OFFER),
                meta(self.price_label),
            ),
        )


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
            "after_login"
        ),
    )


def build_portal_cart_line(
    *,
    cart: Cart,
    cart_line_id: int,
    language_code: str | None = None,
) -> PortalCartLine | None:
    """One line of the cart, drawn alone (the quick add puts it in the
    page without reloading it)."""

    return next(
        iter(
            build_portal_cart_lines(
                cart=cart,
                cart_line_ids=(cart_line_id,),
                language_code=language_code,
            )
        ),
        None,
    )


def build_portal_cart_lines(
    *,
    cart: Cart,
    cart_line_ids: tuple[int, ...],
    language_code: str | None = None,
) -> tuple[PortalCartLine, ...]:
    """Some lines of the cart, in the order of the ids given ("Order
    again" puts them in the page without reloading it)."""

    lines_by_id = {
        line.cart_line_id: line
        for line in _build_portal_cart_lines(
            cart=cart,
            language_code=language_code,
            cart_line_ids=cart_line_ids,
        )
    }

    return tuple(
        lines_by_id[line_id]
        for line_id in cart_line_ids
        if line_id in lines_by_id
    )


def _build_portal_cart_lines(
    *,
    cart: Cart,
    language_code: str | None,
    cart_line_ids: tuple[int, ...] | None = None,
) -> tuple[PortalCartLine, ...]:
    lines = cart.lines.all()

    if cart_line_ids is not None:
        lines = lines.filter(pk__in=cart_line_ids)

    lines = (
        lines
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
                product_url=reverse(
                    "business_portal:catalog_product",
                    kwargs={
                        "product_id": (
                            line.commercial_price.product_id
                        ),
                    },
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

