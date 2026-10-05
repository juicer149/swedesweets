from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.urls import reverse

from carts.models import Cart, CartLine
from pricing.models import PriceAmount
from products.images import product_image_url


@dataclass(frozen=True, slots=True)
class RetailCartLine:
    cart_line_id: int
    product_label: str
    product_url: str
    image_url: str | None
    offer_label: str | None
    unit_price_label: str | None
    line_total_label: str | None
    quantity: int
    quantity_url: str
    remove_url: str


@dataclass(frozen=True, slots=True)
class RetailCartContext:
    cart_lines: tuple[RetailCartLine, ...]
    subtotal_label: str | None
    continue_shopping_url: str
    checkout_url: str | None
    open_payment_url: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "cart_lines": self.cart_lines,
            "subtotal_label": self.subtotal_label,
            "continue_shopping_url": self.continue_shopping_url,
            "checkout_url": self.checkout_url,
            "open_payment_url": self.open_payment_url,
        }

    def line(
        self,
        cart_line_id: int,
    ) -> RetailCartLine | None:
        return next(
            (
                line
                for line in self.cart_lines
                if line.cart_line_id == cart_line_id
            ),
            None,
        )


def build_retail_cart_context(
    *,
    cart: Cart | None,
    checkout_url: str | None = None,
    open_payment_url: str | None = None,
) -> RetailCartContext:
    """Build the cart page.

    While a payment for this cart is open, the cart is read-only and the
    buyer is pointed to that payment instead of to a new checkout.
    """

    cart_lines = (
        _load_cart_lines(
            cart=cart,
        )
        if cart is not None
        else []
    )

    built_lines: list[RetailCartLine] = []
    subtotal: Decimal | None = Decimal("0.00")

    for line in cart_lines:
        unit_price = _eur_price(
            line
        )
        line_total = (
            unit_price * line.quantity
            if unit_price is not None
            else None
        )

        if line_total is None:
            subtotal = None
        elif subtotal is not None:
            subtotal += line_total

        built_lines.append(
            _build_line(
                line=line,
                unit_price=unit_price,
                line_total=line_total,
            )
        )

    return RetailCartContext(
        cart_lines=tuple(
            built_lines
        ),
        subtotal_label=(
            _format_eur(subtotal)
            if built_lines and subtotal is not None
            else None
        ),
        continue_shopping_url=reverse(
            "storefront:product_list"
        ),
        checkout_url=(
            checkout_url
            if built_lines and open_payment_url is None
            else None
        ),
        open_payment_url=open_payment_url,
    )


def _load_cart_lines(
    *,
    cart: Cart,
) -> list[CartLine]:
    return list(
        cart.lines
        .select_related(
            "commercial_price__product",
            "commercial_price__product__profile",
        )
        .prefetch_related(
            "commercial_price__amounts",
        )
        .order_by("id")
    )


def _build_line(
    *,
    line: CartLine,
    unit_price: Decimal | None,
    line_total: Decimal | None,
) -> RetailCartLine:
    commercial_price = line.commercial_price
    product = commercial_price.product

    return RetailCartLine(
        cart_line_id=line.id,
        product_label=product.display_name,
        product_url=reverse(
            "storefront:product_detail",
            kwargs={
                "product_id": product.id,
            },
        ),
        image_url=product_image_url(
            product,
        ),
        offer_label=(
            commercial_price.get_reason_display()
            if commercial_price.reason
            else None
        ),
        unit_price_label=(
            _format_eur(unit_price)
            if unit_price is not None
            else None
        ),
        line_total_label=(
            _format_eur(line_total)
            if line_total is not None
            else None
        ),
        quantity=line.quantity,
        quantity_url=reverse(
            "storefront:set_cart_line_quantity",
            kwargs={
                "cart_line_id": line.id,
            },
        ),
        remove_url=reverse(
            "storefront:remove_cart_line",
            kwargs={
                "cart_line_id": line.id,
            },
        ),
    )


def _eur_price(
    line: CartLine,
) -> Decimal | None:
    for amount in line.commercial_price.amounts.all():
        if amount.currency == PriceAmount.Currency.EUR:
            return amount.price

    return None


def _format_eur(
    value: Decimal,
) -> str:
    return f"€{value:.2f}"
