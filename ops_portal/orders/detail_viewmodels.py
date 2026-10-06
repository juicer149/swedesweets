from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from django.urls import reverse

from accounts.roles import RoleSpec
from common.detail_cards import (
    ACTION_METHOD_GET,
    ACTION_METHOD_POST,
    ACTION_TONE_DELIVER,
    ACTION_TONE_PACK,
    DetailAction,
    build_secondary_get_action,
)
from fulfillment.datatypes import PickLine
from fulfillment.selectors import get_packaging_list
from ops_portal.orders.access import (
    can_cancel_order,
    can_deliver_order,
    can_edit_order,
    can_pack_order,
)
from ops_portal.orders.checklist import list_checked_allocation_ids_for_order
from ops_portal.orders.presentation import (
    maps_directions_href,
    order_status_icon,
    quantity_label,
)
from orders.models import Order, OrderLine
from products.images import product_image_url
from products.models import Product

CUSTOMER_LABEL = "Customer"
RETAIL_BUYER_LABEL = "Retail buyer"


@dataclass(frozen=True, slots=True)
class OrderContentLine:
    product: Product
    product_detail_href: str
    quantity: int
    quantity_label: str
    unit: str
    catalog_label: str
    image_url: str | None


@dataclass(frozen=True, slots=True)
class OrderDate:
    label: str
    value: datetime
    by: object | None = None


@dataclass(frozen=True, slots=True)
class OrderDetailContext:
    order: Order
    content_lines: list[OrderContentLine]
    product_count: int
    total_quantity: int
    total_quantity_label: str
    contents_label: str
    dates: tuple[OrderDate, ...]
    status_label: str
    status_icon: str
    title: str
    description: str
    cancel_url: str
    order_url: str
    customer_maps_href: str
    customer_detail_href: str | None
    buyer_label: str
    pick_lines: list[PickLine]
    checked_allocation_ids: frozenset[int]
    primary_action: DetailAction | None
    secondary_actions: tuple[DetailAction, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "order": self.order,
            "content_lines": self.content_lines,
            "product_count": self.product_count,
            "total_quantity": self.total_quantity,
            "total_quantity_label": self.total_quantity_label,
            "contents_label": self.contents_label,
            "dates": self.dates,
            "status_label": self.status_label,
            "status_icon": self.status_icon,
            "title": self.title,
            "description": self.description,
            "cancel_url": self.cancel_url,
            "order_url": self.order_url,
            "customer_maps_href": self.customer_maps_href,
            "customer_detail_href": self.customer_detail_href,
            "buyer_label": self.buyer_label,
            "pick_lines": self.pick_lines,
            "checked_allocation_ids": self.checked_allocation_ids,
            "primary_action": self.primary_action,
            "secondary_actions": self.secondary_actions,
        }


def build_order_detail_context(
    *,
    order: Order,
    title: str,
    description: str,
    cancel_url: str,
    primary_action: DetailAction | None = None,
    secondary_actions: tuple[DetailAction, ...] = (),
    pick_lines: list[PickLine] | None = None,
) -> OrderDetailContext:
    """Build the context shared by the order's detail, pack, deliver and
    cancel pages.

    The checklist only makes sense while the order is PLACED - that is
    the only status where reservations are still RESERVED rather than
    CONSUMED (packed) or released (delivered/cancelled). pick_lines and
    checked_allocation_ids are both skipped entirely for any other
    status, so no unnecessary queries run.

    pack() passes its own pre-fetched pick_lines (it already needs the
    list to decide whether the confirm button is disabled), which
    skips the redundant query here.
    """

    is_placed = order.status == Order.Status.PLACED

    if pick_lines is None:
        pick_lines = get_packaging_list(order=order) if is_placed else []

    checked_allocation_ids = (
        list_checked_allocation_ids_for_order(order=order)
        if is_placed
        else frozenset()
    )

    order_lines = list(
        order.lines.select_related(
            "product",
            "product__profile",
        ).all()
    )
    content_lines = _build_content_lines(order_lines)
    product_count = len(content_lines)
    total_quantity = sum(line.quantity for line in content_lines)
    total_quantity_text = quantity_label(total_quantity)

    return OrderDetailContext(
        order=order,
        content_lines=content_lines,
        product_count=product_count,
        total_quantity=total_quantity,
        total_quantity_label=total_quantity_text,
        contents_label=(
            f"{product_count} product{'' if product_count == 1 else 's'}"
            f" · {total_quantity_text}"
        ),
        dates=_order_dates(order),
        status_label=order.get_status_display(),
        status_icon=order_status_icon(order.status),
        title=title,
        description=description,
        cancel_url=cancel_url,
        order_url=order_detail_href(order),
        customer_maps_href=maps_directions_href(order.customer_address),
        customer_detail_href=customer_detail_href(order),
        buyer_label=buyer_label(order),
        pick_lines=pick_lines,
        checked_allocation_ids=checked_allocation_ids,
        primary_action=primary_action,
        secondary_actions=secondary_actions,
    )


def _order_dates(order: Order) -> tuple[OrderDate, ...]:
    """Every step the order has passed, in order, with who did it."""

    steps = (
        ("Created", order.created_at, None),
        ("Placed", order.placed_at, order.placed_by),
        ("Last edited", order.edited_at, order.edited_by),
        ("Packed", order.packed_at, order.packed_by),
        ("Delivered", order.delivered_at, order.delivered_by),
        ("Cancelled", order.cancelled_at, order.cancelled_by),
    )

    return tuple(
        OrderDate(label=label, value=value, by=by)
        for label, value, by in steps
        if value is not None
    )


def build_order_detail_primary_action(
    *,
    order: Order,
    role_spec: RoleSpec,
) -> DetailAction | None:
    if can_pack_order(order=order, role_spec=role_spec):
        return build_go_to_pack_action(
            href=order_pack_href(order),
        )

    if can_deliver_order(order=order, role_spec=role_spec):
        return build_go_to_deliver_action(
            href=order_deliver_href(order),
        )

    return None


def build_order_secondary_actions(
    *,
    order: Order,
    role_spec: RoleSpec,
) -> tuple[DetailAction, ...]:
    """Return the secondary actions shown on the detail and pack pages.

    For editable orders, Cancel order deliberately lives only on the edit
    page (see OrderFormContext.cancel_order_url), not here - cancelling is
    a more consequential action than viewing/packing, and edit is already
    the page a person goes to when they intend to change something about
    the order.

    Retail orders cannot be edited, so their cancel action is offered here
    instead.
    """

    actions: list[DetailAction] = []

    if can_edit_order(order=order, role_spec=role_spec):
        actions.append(
            build_secondary_get_action(
                label="Edit order",
                href=order_edit_href(order),
            )
        )
    elif (
        order.channel == Order.Channel.RETAIL
        and can_cancel_order(order=order, role_spec=role_spec)
    ):
        actions.append(
            build_secondary_get_action(
                label="Cancel order",
                href=order_cancel_href(order),
            )
        )

    return tuple(actions)


def build_order_cancel_back_url(
    *,
    order: Order,
    role_spec: RoleSpec,
) -> str:
    if can_edit_order(order=order, role_spec=role_spec):
        return order_edit_href(order)

    if can_pack_order(order=order, role_spec=role_spec):
        return order_pack_href(order)

    if can_deliver_order(order=order, role_spec=role_spec):
        return order_deliver_href(order)

    return order_detail_href(order)


def build_post_edit_success_url(
    *,
    order: Order,
    role_spec: RoleSpec,
) -> str:
    if can_pack_order(order=order, role_spec=role_spec):
        return order_pack_href(order)

    return order_detail_href(order)


def build_post_pack_success_url(
    *,
    order: Order,
    role_spec: RoleSpec,
) -> str:
    if can_deliver_order(order=order, role_spec=role_spec):
        return order_deliver_href(order)

    return order_detail_href(order)


def build_go_to_pack_action(*, href: str) -> DetailAction:
    return DetailAction(
        label="Pack order",
        href=href,
        icon="box",
        method=ACTION_METHOD_GET,
        tone=ACTION_TONE_PACK,
    )


def build_go_to_deliver_action(*, href: str) -> DetailAction:
    return DetailAction(
        label="Mark delivered",
        href=href,
        icon="truck",
        method=ACTION_METHOD_GET,
        tone=ACTION_TONE_DELIVER,
    )


def build_pack_action(*, is_disabled: bool = False) -> DetailAction:
    return DetailAction(
        label="Confirm packed",
        icon="box",
        method=ACTION_METHOD_POST,
        tone=ACTION_TONE_PACK,
        client_behavior="pack-checklist",
        is_disabled=is_disabled,
    )


def build_deliver_action() -> DetailAction:
    return DetailAction(
        label="Confirm delivered",
        icon="truck",
        method=ACTION_METHOD_POST,
        tone=ACTION_TONE_DELIVER,
    )


def order_detail_href(order: Order) -> str:
    return reverse("ops_orders:detail", kwargs={"order_id": order.pk})


def order_edit_href(order: Order) -> str:
    return reverse("ops_orders:edit", kwargs={"order_id": order.pk})


def order_cancel_href(order: Order) -> str:
    return reverse("ops_orders:cancel", kwargs={"order_id": order.pk})


def order_pack_href(order: Order) -> str:
    return reverse("ops_orders:pack", kwargs={"order_id": order.pk})


def order_deliver_href(order: Order) -> str:
    return reverse("ops_orders:deliver", kwargs={"order_id": order.pk})


def customer_detail_href(order: Order) -> str | None:
    """Link to the customer page, or None for orders without a customer.

    Retail orders are placed by anonymous buyers whose details live only
    in the order's buyer snapshot.
    """

    if order.customer_id is None:
        return None

    return reverse("ops_customers:detail", kwargs={"customer_pk": order.customer_id})


def buyer_label(order: Order) -> str:
    """Label for who placed the order: a customer or a retail buyer."""

    if order.customer_id is None:
        return RETAIL_BUYER_LABEL

    return CUSTOMER_LABEL


def product_detail_href(product_id: int) -> str:
    return reverse("ops_products:detail", kwargs={"product_pk": product_id})


def _build_content_lines(lines: list[OrderLine]) -> list[OrderContentLine]:
    content_lines: list[OrderContentLine] = []

    for line in lines:
        line_product_detail_href = product_detail_href(line.product_id)
        quantity_text = line.product.stock_quantity_label(line.quantity_in_units)

        content_lines.append(
            OrderContentLine(
                product=line.product,
                product_detail_href=line_product_detail_href,
                quantity=line.quantity_in_units,
                quantity_label=quantity_text,
                unit=line.get_unit_display(),
                catalog_label=line.product.catalog_label,
                image_url=product_image_url(line.product),
            )
        )

    return content_lines
