from __future__ import annotations

from dataclasses import dataclass

from django.urls import reverse

from accounts.roles import RoleSpec
from common.page_header import PageHeader, PageHeaderAction
from common.table_tools import build_query_url
from common.ui import (
    StatusPresentation,
)
from ops_portal.orders.access import (
    can_create_order,
    can_deliver_order,
    can_pack_order,
)
from ops_portal.orders.presentation import (
    build_order_status_presentation,
    order_lifecycle_label,
    order_quantity_label,
)
from orders.models import Order


@dataclass(frozen=True, slots=True)
class OrderChannelLink:
    key: str
    label: str
    href: str
    is_active: bool


def build_order_channel_tabs(
    *,
    active_channel: str,
) -> tuple[OrderChannelLink, ...]:
    return tuple(
        OrderChannelLink(
            key=value,
            label=label,
            href=_order_channel_href(value),
            is_active=value == active_channel,
        )
        for value, label in Order.Channel.choices
    )


def _order_channel_href(channel: str) -> str:
    return build_query_url(
        base_path=reverse("ops_orders:index"),
        params={"channel": channel},
    )


@dataclass(frozen=True, slots=True)
class OrderPageRow:
    order: Order
    status: StatusPresentation
    detail_href: str
    total_quantity: int
    # Phones: a .line--link row ("#31 · customer", "Placed 2 h ago", units).
    title: str
    meta: str
    quantity_label: str

    @property
    def link_label(self) -> str:
        return (
            f"Order #{self.order.pk}, {self.order.customer_name}, "
            f"{self.status.label}"
        )


def build_orders_page_header(*, role_spec: RoleSpec) -> PageHeader:
    return PageHeader(
        title="Orders",
        title_id="orders-title",
        action=_build_create_order_header_action(role_spec),
    )


def build_order_page_rows(
    *,
    orders: list[Order],
    role_spec: RoleSpec,
) -> list[OrderPageRow]:
    return [
        _build_order_page_row(
            order=order,
            role_spec=role_spec,
        )
        for order in orders
    ]


def _build_order_page_row(
    *,
    order: Order,
    role_spec: RoleSpec,
) -> OrderPageRow:
    status = _order_status(order)
    detail_href = _order_detail_href(
        order=order,
        role_spec=role_spec,
    )
    total_quantity = getattr(order, "total_quantity", 0)

    return OrderPageRow(
        order=order,
        status=status,
        detail_href=detail_href,
        total_quantity=total_quantity,
        title=f"#{order.pk} · {order.customer_name}",
        meta=order_lifecycle_label(order),
        quantity_label=order_quantity_label(order),
    )


def _build_create_order_header_action(
    role_spec: RoleSpec,
) -> PageHeaderAction | None:
    if not can_create_order(role_spec=role_spec):
        return None

    return PageHeaderAction(
        label="Place order",
        href=_create_order_href(),
        icon="cart",
        aria_label="Place a new order",
    )


def _order_status(order: Order) -> StatusPresentation:
    return build_order_status_presentation(order.status)


def _order_detail_href(
    *,
    order: Order,
    role_spec: RoleSpec,
) -> str:
    if can_pack_order(order=order, role_spec=role_spec):
        return _pack_order_href(order)

    if can_deliver_order(order=order, role_spec=role_spec):
        return _deliver_order_href(order)

    return _order_detail_base_href(order)


def _create_order_href() -> str:
    return reverse("ops_orders:create")


def _order_detail_base_href(order: Order) -> str:
    return reverse("ops_orders:detail", kwargs={"order_id": order.pk})


def _pack_order_href(order: Order) -> str:
    return reverse("ops_orders:pack", kwargs={"order_id": order.pk})


def _deliver_order_href(order: Order) -> str:
    return reverse("ops_orders:deliver", kwargs={"order_id": order.pk})
