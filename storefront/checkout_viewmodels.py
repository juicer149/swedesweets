from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.urls import reverse

from products.images import product_image_url
from retail.models import RetailCheckoutSession


@dataclass(frozen=True, slots=True)
class CheckoutReviewLine:
    product_label: str
    image_url: str | None
    quantity: int
    unit_price_label: str
    line_total_label: str


@dataclass(frozen=True, slots=True)
class CheckoutBuyer:
    name: str
    email: str
    phone_number: str
    address_line: str
    postal_code: str
    city: str


@dataclass(frozen=True, slots=True)
class CheckoutReviewContext:
    lines: tuple[CheckoutReviewLine, ...]
    total_label: str
    buyer: CheckoutBuyer
    edit_details_url: str
    cart_url: str
    pay_url: str
    cancel_payment_url: str
    has_open_payment: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "lines": self.lines,
            "total_label": self.total_label,
            "buyer": self.buyer,
            "edit_details_url": self.edit_details_url,
            "cart_url": self.cart_url,
            "pay_url": self.pay_url,
            "cancel_payment_url": self.cancel_payment_url,
            "has_open_payment": self.has_open_payment,
        }


def build_checkout_review_context(
    *,
    checkout: RetailCheckoutSession,
    has_open_payment: bool = False,
) -> CheckoutReviewContext:
    order = checkout.order

    order_lines = list(
        order.lines
        .select_related(
            "product",
            "product__profile",
        )
        .order_by("id")
    )

    lines: list[CheckoutReviewLine] = []
    total = Decimal("0.00")

    for line in order_lines:
        quantity = int(
            line.quantity_in_units
        )
        line_total = (
            line.unit_price_snapshot
            * quantity
        )
        total += line_total

        lines.append(
            CheckoutReviewLine(
                product_label=line.product.display_name,
                image_url=product_image_url(
                    line.product,
                ),
                quantity=quantity,
                unit_price_label=_format_eur(
                    line.unit_price_snapshot
                ),
                line_total_label=_format_eur(
                    line_total
                ),
            )
        )

    return CheckoutReviewContext(
        lines=tuple(
            lines
        ),
        total_label=_format_eur(
            total
        ),
        buyer=CheckoutBuyer(
            name=order.buyer_name_snapshot,
            email=order.buyer_email_snapshot,
            phone_number=order.buyer_phone_snapshot,
            address_line=order.buyer_address_line_snapshot,
            postal_code=order.buyer_postal_code_snapshot,
            city=order.buyer_city_snapshot,
        ),
        edit_details_url=reverse(
            "storefront:checkout"
        ),
        cart_url=reverse(
            "storefront:cart"
        ),
        pay_url=reverse(
            "storefront:checkout_pay",
            kwargs={
                "checkout_id": checkout.pk,
            },
        ),
        cancel_payment_url=reverse(
            "storefront:checkout_cancel_payment",
            kwargs={
                "checkout_id": checkout.pk,
            },
        ),
        has_open_payment=has_open_payment,
    )


def _format_eur(
    value: Decimal,
) -> str:
    return f"€{value:.2f}"
