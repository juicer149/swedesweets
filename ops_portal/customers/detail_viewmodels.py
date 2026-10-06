from __future__ import annotations

from dataclasses import dataclass

from django.urls import reverse

from accounts.roles import RoleSpec
from common.page_tabs import PageTab
from common.ui import StatusPresentation
from customers.models import Customer
from ops_portal.customers.access import can_edit_customer
from ops_portal.customers.presentation import (
    customer_place_label,
    customer_status_icon,
    customer_status_key,
    customer_status_label,
)
from ops_portal.orders.presentation import (
    build_order_status_presentation,
    maps_directions_href,
    order_lifecycle_label,
    order_quantity_label,
)
from orders.models import Order
from orders.selectors import CustomerOrderSummary

CUSTOMER_DETAIL_TABS = (
    PageTab(
        key="customer",
        label="Customer",
        icon="users",
        template="ops_portal/customers/includes/detail_tab_customer.html",
    ),
    PageTab(
        key="orders",
        label="Orders",
        icon="cart",
        template="ops_portal/customers/includes/detail_tab_orders.html",
    ),
)


@dataclass(frozen=True, slots=True)
class CustomerOrderRow:
    """One of the customer's orders as a .line--link row."""

    order_id: int
    href: str
    status: StatusPresentation
    meta: str
    quantity_label: str

    @property
    def title(self) -> str:
        return f"#{self.order_id}"

    @property
    def link_label(self) -> str:
        return f"Order #{self.order_id}, {self.status.label}"


@dataclass(frozen=True, slots=True)
class CustomerDetailContext:
    customer: Customer
    order_summary: CustomerOrderSummary
    order_rows: list[CustomerOrderRow]
    maps_href: str
    edit_href: str | None
    back_url: str

    def as_dict(self) -> dict[str, object]:
        return {
            "customer": self.customer,
            "order_summary": self.order_summary,
            "orders_label": _orders_label(self.order_summary.total_orders),
            "order_rows": self.order_rows,
            "maps_href": self.maps_href,
            "edit_href": self.edit_href,
            "title": self.customer.name,
            "status_key": customer_status_key(self.customer),
            "status_label": customer_status_label(self.customer),
            "status_icon": customer_status_icon(self.customer),
            "place_label": customer_place_label(self.customer),
            "page_tabs": CUSTOMER_DETAIL_TABS,
            "tabs_label": "Customer sections",
            "back_url": self.back_url,
            "back_label": "Back to customers",
        }


def build_customer_detail_context(
    *,
    customer: Customer,
    order_summary: CustomerOrderSummary,
    orders: list[Order],
    role_spec: RoleSpec,
    back_url: str,
) -> CustomerDetailContext:
    return CustomerDetailContext(
        customer=customer,
        order_summary=order_summary,
        order_rows=[_build_order_row(order) for order in orders],
        maps_href=maps_directions_href(customer.address),
        edit_href=(
            reverse("ops_customers:edit", kwargs={"customer_pk": customer.pk})
            if can_edit_customer(customer=customer, role_spec=role_spec)
            else None
        ),
        back_url=back_url,
    )


def _build_order_row(order: Order) -> CustomerOrderRow:
    return CustomerOrderRow(
        order_id=order.id,
        href=reverse("ops_orders:detail", kwargs={"order_id": order.id}),
        status=build_order_status_presentation(order.status),
        meta=order_lifecycle_label(order),
        quantity_label=order_quantity_label(order),
    )


def _orders_label(total_orders: int) -> str:
    if total_orders == 1:
        return "1 order"

    return f"{total_orders} orders"
