"""A customer's last few orders on the ops order form, above its product
search (includes/orders/recent_orders.html, mode "form"): "Order again"
and each product's "+" add lines to the form in the page
(order_lines.js), each carrying its offer as a new line shows it.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass

from common.lines import META_OFFER, LineView, meta, metas
from customers.models import Customer
from ops_portal.orders.forms import (
    OrderLineOfferView,
    build_order_line_offer_view,
)
from orders.models import OrderLine
from orders.selectors import list_recent_business_orders

RECENT_ORDER_COUNT = 3

NOT_AVAILABLE_LABEL = "Not available right now"


@dataclass(frozen=True, slots=True)
class OpsRecentOrderLine:
    offer: OrderLineOfferView
    quantity: int
    # The offer the "+" adds, or None when it cannot be chosen now.
    commercial_price_id: int | None

    @property
    def name(self) -> str:
        return self.offer.name

    @property
    def view(self) -> LineView:
        return LineView(
            name=self.offer.name,
            image_url=self.offer.image_url,
            metas=metas(
                meta(self.offer.meta),
                meta(self.offer.offer_detail, META_OFFER),
                meta(
                    None
                    if self.commercial_price_id
                    else NOT_AVAILABLE_LABEL
                ),
            ),
            aside=f"× {self.quantity}",
        )


@dataclass(frozen=True, slots=True)
class OpsRecentOrder:
    order_id: int
    date_label: str
    lines: tuple[OpsRecentOrderLine, ...]

    @property
    def title(self) -> str:
        return f"Order #{self.order_id}"

    @property
    def summary(self) -> str:
        count = len(self.lines)
        return f"{count} product" if count == 1 else f"{count} products"


def build_ops_recent_orders(
    *,
    customer: Customer,
    selectable_offer_ids: Collection[int],
    exclude_order_id: int | None = None,
    limit: int = RECENT_ORDER_COUNT,
) -> tuple[OpsRecentOrder, ...]:
    """The customer's latest orders; a line's "+" only for an offer the
    form can choose now (selectable_offer_ids)."""

    return tuple(
        OpsRecentOrder(
            order_id=order.pk,
            date_label=order.created_at.date().isoformat(),
            lines=tuple(
                _line(
                    line,
                    selectable_offer_ids=selectable_offer_ids,
                )
                for line in sorted(
                    order.lines.all(),
                    key=lambda line: line.pk,
                )
            ),
        )
        for order in list_recent_business_orders(
            customer=customer,
            limit=limit,
            exclude_order_id=exclude_order_id,
        )
    )


def _line(
    line: OrderLine,
    *,
    selectable_offer_ids: Collection[int],
) -> OpsRecentOrderLine:
    return OpsRecentOrderLine(
        offer=build_order_line_offer_view(line.commercial_offer),
        quantity=line.quantity_in_units,
        commercial_price_id=(
            line.commercial_offer_id
            if line.commercial_offer_id in selectable_offer_ids
            else None
        ),
    )
