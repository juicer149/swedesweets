from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from business_portal.orders.presentation import (
    build_order_status_presentation,
    quantity_label,
)
from common.ui import StatusPresentation
from orders.models import Order


@dataclass(frozen=True, slots=True)
class PortalOrderPageRow:
    order: Order
    status: StatusPresentation
    detail_href: str
    total_quantity: int
    created_at_label: str

    # Phones: a .line--link row ("Order #31", "Placed · 2026-10-06", units).
    @property
    def title(self) -> str:
        return _("Order #%(order_id)s") % {"order_id": self.order.pk}

    @property
    def meta(self) -> str:
        return f"{self.status.label} · {self.created_at_label}"

    @property
    def quantity_label(self) -> str:
        return quantity_label(self.total_quantity)


def build_portal_order_page_rows(
    *,
    orders: list[Order],
) -> list[PortalOrderPageRow]:
    return [
        PortalOrderPageRow(
            order=order,
            status=build_order_status_presentation(order.status),
            detail_href=_order_detail_href(order),
            total_quantity=getattr(order, "total_quantity", 0),
            created_at_label=date_label(order.created_at),
        )
        for order in orders
    ]


def _order_detail_href(
    order: Order,
) -> str:
    return reverse(
        "business_portal:order_detail",
        kwargs={
            "order_id": order.pk,
        },
    )


def date_label(
    value: datetime,
) -> str:
    return timezone.localtime(
        value
    ).strftime(
        "%Y-%m-%d"
    )
