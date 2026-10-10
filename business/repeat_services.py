from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from business.cart_services import (
    InvalidBusinessCart,
    add_catalog_offer_to_cart,
)
from carts.models import Cart
from customers.models import Customer
from orders.errors import InvalidOrderOperation
from orders.models import Order, OrderLine
from products.models import Product


class RepeatOrderSkipReason(StrEnum):
    PRODUCT_UNAVAILABLE = "product_unavailable"
    OFFER_UNAVAILABLE = "offer_unavailable"


@dataclass(frozen=True, slots=True)
class RepeatOrderSkippedLine:
    product: Product
    quantity: int
    reason: RepeatOrderSkipReason


@dataclass(frozen=True, slots=True)
class RepeatOrderResult:
    cart: Cart | None
    added_count: int
    skipped: tuple[RepeatOrderSkippedLine, ...]
    # The cart lines the repeat added to or created, in the order's order
    # (a page can draw them in place).
    added_line_ids: tuple[int, ...] = ()

    @property
    def has_added_lines(self) -> bool:
        return self.added_count > 0


def repeat_order_into_cart(
    *,
    customer: Customer,
    source_order: Order,
) -> RepeatOrderResult:
    """Copy currently eligible selections from a historical order into the cart.

    Repeat restores purchase intent, not orderability at this instant.

    Current stock and per-order quantity limits therefore do not constrain the
    repeat operation. They are validated when the cart is converted into an
    order and placed.

    Every durable OrderLine already records its selected CommercialPrice.
    Repeating an order preserves that commercial identity when the offer is
    still eligible for BUSINESS ordering.
    """

    _require_repeatable_order(
        customer=customer,
        source_order=source_order,
    )

    source_lines = tuple(
        source_order.lines
        .select_related(
            "product",
            "commercial_offer",
        )
        .order_by("id")
    )

    cart: Cart | None = None
    added_count = 0
    skipped: list[RepeatOrderSkippedLine] = []
    added_line_ids: list[int] = []

    for line in source_lines:
        if not line.product.active:
            skipped.append(
                _skipped(
                    line=line,
                    reason=(
                        RepeatOrderSkipReason.PRODUCT_UNAVAILABLE
                    ),
                )
            )
            continue

        try:
            cart_line = add_catalog_offer_to_cart(
                customer=customer,
                product=line.product,
                commercial_price_id=(
                    line.commercial_offer_id
                ),
                quantity=line.quantity_in_units,
            )
        except InvalidBusinessCart:
            skipped.append(
                _skipped(
                    line=line,
                    reason=(
                        RepeatOrderSkipReason.OFFER_UNAVAILABLE
                    ),
                )
            )
            continue

        cart = cart_line.cart
        added_count += 1

        if cart_line.pk not in added_line_ids:
            added_line_ids.append(cart_line.pk)

    return RepeatOrderResult(
        cart=cart,
        added_count=added_count,
        skipped=tuple(skipped),
        added_line_ids=tuple(added_line_ids),
    )


def _require_repeatable_order(
    *,
    customer: Customer,
    source_order: Order,
) -> None:
    if (
        source_order.channel
        != Order.Channel.BUSINESS
    ):
        raise InvalidOrderOperation(
            "order is not a business order"
        )

    if source_order.customer_id != customer.id:
        raise InvalidOrderOperation(
            "order does not belong to the current customer"
        )

    if source_order.status == Order.Status.DRAFT:
        raise InvalidOrderOperation(
            "draft orders cannot be repeated"
        )


def _skipped(
    *,
    line: OrderLine,
    reason: RepeatOrderSkipReason,
) -> RepeatOrderSkippedLine:
    return RepeatOrderSkippedLine(
        product=line.product,
        quantity=line.quantity_in_units,
        reason=reason,
    )
