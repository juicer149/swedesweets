from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from django.urls import reverse

from accounts.roles import AccountRole, Capability, RoleSpec
from inventory.selectors import (
    count_expiring_batches,
    list_expiring_batch_rows_for_dashboard,
)
from ops_portal.dashboard.viewmodels import DashboardQueue, DashboardQueueItem
from ops_portal.inventory.presentation import (
    batch_quantity_label,
    product_available_quantity_label,
)
from ops_portal.orders.presentation import (
    order_lifecycle_label,
    order_quantity_label,
)
from orders.models import Order
from orders.selectors import (
    count_packed_orders,
    count_placed_orders,
    list_packed_orders_for_dashboard,
    list_placed_orders_for_dashboard,
)
from reservations.availability import (
    count_low_stock_products,
    list_low_stock_products_for_dashboard,
)

QUEUE_PREVIEW_LIMIT = 4


# -----------------------------------------------------------------------------
# Queue specification
#
# A DashboardQueueSpec defines one possible dashboard queue.
#
# AccountRole chooses a queue family.
# RoleSpec filters each queue by capability.
# The generic builder below turns the selected specs into queues.


@dataclass(frozen=True, slots=True)
class DashboardQueueSpec:
    key: str
    title: str
    capability: Capability
    tone: str
    view_all_label: str

    count_items: Callable[[], int]
    list_items: Callable[[], Iterable[object]]
    build_item: Callable[[object], DashboardQueueItem]
    build_view_all_href: Callable[[], str]

    def build(self, *, count: int) -> DashboardQueue:
        return DashboardQueue(
            key=self.key,
            title=self.title,
            count=count,
            tone=self.tone,
            items=tuple(self.build_item(item) for item in self.list_items()),
            view_all_href=self.build_view_all_href(),
            view_all_label=self.view_all_label,
        )


# -----------------------------------------------------------------------------
# Query callbacks
#
# These callbacks keep queue specs readable.
#
# Domain defaults such as EXPIRY_SOON_DAYS and LOW_STOCK_THRESHOLD live in their
# own domains. Dashboard owns only QUEUE_PREVIEW_LIMIT, because that is a UI
# preview concern.


def _list_placed_orders() -> Iterable[object]:
    return list_placed_orders_for_dashboard(limit=QUEUE_PREVIEW_LIMIT)


def _list_packed_orders() -> Iterable[object]:
    return list_packed_orders_for_dashboard(limit=QUEUE_PREVIEW_LIMIT)


def _list_expiring_batches() -> Iterable[object]:
    return list_expiring_batch_rows_for_dashboard(
        limit=QUEUE_PREVIEW_LIMIT,
    )


def _list_low_stock_products() -> Iterable[object]:
    return list_low_stock_products_for_dashboard(
        limit=QUEUE_PREVIEW_LIMIT,
    )


# -----------------------------------------------------------------------------
# View-all href callbacks


def _placed_orders_view_all_href() -> str:
    return f"{reverse('ops_orders:index')}?status={Order.Status.PLACED}#orders-list"


def _packed_orders_view_all_href() -> str:
    return f"{reverse('ops_orders:index')}?status={Order.Status.PACKED}#orders-list"


def _expiring_batches_view_all_href() -> str:
    return f"{reverse('ops_inventory:index')}?sort=best_before#inventory-list"


def _low_stock_products_view_all_href() -> str:
    index = reverse("ops_inventory:index")
    return f"{index}?view=products&sort=available#inventory-list"


# -----------------------------------------------------------------------------
# Item builders
#
# These functions adapt domain rows/models into DashboardQueueItem viewmodels.


def _placed_order_item(order) -> DashboardQueueItem:
    return DashboardQueueItem(
        title=f"#{order.pk} · {order.customer_name}",
        meta=f"{order_lifecycle_label(order)} · {order_quantity_label(order)}",
        href=reverse("ops_orders:pack", kwargs={"order_id": order.pk}),
        action_label="Pack order →",
        tone="warning",
        icon="cart",
    )


def _packed_order_item(order) -> DashboardQueueItem:
    return DashboardQueueItem(
        title=f"#{order.pk} · {order.customer_name}",
        meta=f"{order_lifecycle_label(order)} · {order_quantity_label(order)}",
        href=reverse("ops_orders:deliver", kwargs={"order_id": order.pk}),
        action_label="Mark delivered →",
        tone="info",
        icon="packed",
    )


def _expiring_batch_item(row) -> DashboardQueueItem:
    batch = row.batch

    return DashboardQueueItem(
        title=f"{batch.batch_id} · {batch.product.display_name}",
        meta=(
            f"{batch_quantity_label(batch)} · "
            f"{row.expiry.label} {batch.best_before:%Y-%m-%d}"
        ),
        href=reverse("ops_inventory:detail", kwargs={"batch_pk": batch.pk}),
        action_label="Open batch →",
        tone="danger",
        icon="warning",
    )


def _low_stock_item(row) -> DashboardQueueItem:
    return DashboardQueueItem(
        title=f"{row.code_label} · {row.product_name}",
        meta=product_available_quantity_label(row),
        href=reverse("ops_products:detail", kwargs={"product_pk": row.product_id}),
        action_label="Open product →",
        tone="warning",
        icon="inventory",
    )


# -----------------------------------------------------------------------------
# Available queues
#
# Add new dashboard queues here. Each queue is filtered by capability before it
# can appear on the dashboard.


PLACED_ORDERS_QUEUE = DashboardQueueSpec(
    key="placed",
    capability=Capability.PACK_ORDERS,
    tone="warning",
    title="Placed orders",
    view_all_label="View all placed orders →",
    count_items=count_placed_orders,
    list_items=_list_placed_orders,
    build_item=_placed_order_item,
    build_view_all_href=_placed_orders_view_all_href,
)

PACKED_ORDERS_QUEUE = DashboardQueueSpec(
    key="packed",
    capability=Capability.DELIVER_ORDERS,
    tone="info",
    title="Packed orders",
    view_all_label="View all packed orders →",
    count_items=count_packed_orders,
    list_items=_list_packed_orders,
    build_item=_packed_order_item,
    build_view_all_href=_packed_orders_view_all_href,
)

EXPIRING_BATCHES_QUEUE = DashboardQueueSpec(
    key="expiring",
    capability=Capability.VIEW_INVENTORY_RISKS,
    tone="danger",
    title="Expiring batches",
    view_all_label="View expiring batches →",
    count_items=count_expiring_batches,
    list_items=_list_expiring_batches,
    build_item=_expiring_batch_item,
    build_view_all_href=_expiring_batches_view_all_href,
)

LOW_STOCK_QUEUE = DashboardQueueSpec(
    key="low-stock",
    capability=Capability.VIEW_INVENTORY_RISKS,
    tone="warning",
    title="Low stock",
    view_all_label="View low stock products →",
    count_items=count_low_stock_products,
    list_items=_list_low_stock_products,
    build_item=_low_stock_item,
    build_view_all_href=_low_stock_products_view_all_href,
)


# -----------------------------------------------------------------------------
# Role-specific queue families
#
# This is UX, not authorization. A role may have access to inventory/products
# while still seeing only order-workflow queues on the dashboard.


OPS_DASHBOARD_QUEUES = (
    PLACED_ORDERS_QUEUE,
    PACKED_ORDERS_QUEUE,
    EXPIRING_BATCHES_QUEUE,
    LOW_STOCK_QUEUE,
)

RESTRICTED_STAFF_DASHBOARD_QUEUES = (
    PLACED_ORDERS_QUEUE,
    PACKED_ORDERS_QUEUE,
)

DASHBOARD_QUEUES_BY_ROLE: dict[
    AccountRole,
    tuple[DashboardQueueSpec, ...],
] = {
    AccountRole.OWNER: OPS_DASHBOARD_QUEUES,
    AccountRole.FULL_STAFF: OPS_DASHBOARD_QUEUES,
    AccountRole.RESTRICTED_STAFF: RESTRICTED_STAFF_DASHBOARD_QUEUES,
}


# -----------------------------------------------------------------------------
# Public builder


def build_dashboard_queues(
    *,
    account_role: AccountRole,
    role_spec: RoleSpec,
) -> tuple[DashboardQueue, ...]:
    """The queues this role sees, in order; empty queues are left out."""
    candidates = DASHBOARD_QUEUES_BY_ROLE.get(account_role, ())
    queues: list[DashboardQueue] = []

    for queue_spec in candidates:
        if not role_spec.allows(queue_spec.capability):
            continue

        count = queue_spec.count_items()

        if count <= 0:
            continue

        queues.append(queue_spec.build(count=count))

    return tuple(queues)
