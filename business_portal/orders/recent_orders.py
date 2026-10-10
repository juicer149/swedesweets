"""A shop's last few orders on its cart page, folded like the FAQ: one row
each ("#31 · 2026-10-06 · 5 products"), "Order again" beside it, and
inside its products, each with a "+" when it can still be ordered.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass

from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from business_portal.orders.list_viewmodels import date_label
from business_portal.orders.product_presentation import (
    business_order_line_presentation,
)
from common.lines import META_OFFER, LineView, meta, metas
from customers.models import Customer
from orders.models import Order, OrderLine
from products.images import product_image_url

RECENT_ORDER_COUNT = 3

NOT_AVAILABLE_LABEL = _("Not available right now")


@dataclass(frozen=True, slots=True)
class RecentOrderLine:
    name: str
    offer_label: str | None
    quantity: int
    image_url: str | None
    # The offer to add with "+", or None when it cannot be ordered now.
    commercial_price_id: int | None

    @property
    def view(self) -> LineView:
        return LineView(
            name=self.name,
            image_url=self.image_url,
            metas=metas(
                meta(self.offer_label, META_OFFER),
                meta(
                    None
                    if self.commercial_price_id
                    else NOT_AVAILABLE_LABEL
                ),
            ),
            aside=f"× {self.quantity}",
        )


@dataclass(frozen=True, slots=True)
class RecentOrder:
    order_id: int
    date_label: str
    lines: tuple[RecentOrderLine, ...]
    repeat_url: str

    @property
    def title(self) -> str:
        return _("Order #%(order_id)s") % {"order_id": self.order_id}

    @property
    def summary(self) -> str:
        return ngettext(
            "%(count)s product",
            "%(count)s products",
            len(self.lines),
        ) % {"count": len(self.lines)}


def build_recent_orders(
    *,
    customer: Customer,
    language_code: str,
    orderable_offer_ids: Collection[int],
    limit: int = RECENT_ORDER_COUNT,
) -> tuple[RecentOrder, ...]:
    """The customer's latest business orders that went through (not
    drafts, not cancelled), newest first."""

    orders = (
        Order.objects
        .filter(
            customer=customer,
            channel=Order.Channel.BUSINESS,
        )
        .exclude(
            status__in=(
                Order.Status.DRAFT,
                Order.Status.CANCELLED,
            )
        )
        .prefetch_related(
            "lines__product__profile",
            "lines__product__translations",
            "lines__commercial_offer",
        )
        .order_by("-created_at", "-id")[:limit]
    )

    return tuple(
        RecentOrder(
            order_id=order.pk,
            date_label=date_label(order.created_at),
            lines=tuple(
                _recent_order_line(
                    line,
                    language_code=language_code,
                    currency=order.currency,
                    orderable_offer_ids=orderable_offer_ids,
                )
                for line in sorted(
                    order.lines.all(),
                    key=lambda line: line.pk,
                )
            ),
            repeat_url=reverse(
                "business_portal:repeat_order",
                kwargs={"order_id": order.pk},
            ),
        )
        for order in orders
    )


def _recent_order_line(
    line: OrderLine,
    *,
    language_code: str,
    currency: str,
    orderable_offer_ids: Collection[int],
) -> RecentOrderLine:
    presentation = business_order_line_presentation(
        line,
        language_code=language_code,
        currency=currency,
    )

    return RecentOrderLine(
        name=presentation.catalog_label,
        offer_label=presentation.offer_label,
        quantity=line.quantity_in_units,
        image_url=product_image_url(line.product),
        commercial_price_id=(
            line.commercial_offer_id
            if line.commercial_offer_id in orderable_offer_ids
            else None
        ),
    )
