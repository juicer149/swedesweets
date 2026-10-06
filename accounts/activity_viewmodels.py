from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from django.utils import timezone
from django.utils.translation import gettext as _

from accounts.activity import (
    AccountActivity,
    AccountActivityKind,
)
from customers.models import Customer
from inventory.models import InventoryBatch
from orders.models import Order
from products.models import Product

# Tones a .line__icon can show; neutral and muted events get the plain grey.
LINE_TONES = frozenset({"warning", "info", "success", "danger"})


@dataclass(frozen=True, slots=True)
class AccountActivityRow:
    """One thing an account did, as a .line--link row:
    "Order #31" / "Placed order · 2026-10-06 14:02" / Café Blanc."""

    name: str
    meta: str
    aside: str
    href: str
    tone: str
    icon: str


def build_account_activity_rows(
    activities: tuple[AccountActivity, ...],
    *,
    href_for: Callable[[AccountActivity], str],
) -> tuple[AccountActivityRow, ...]:
    """href_for: where each row leads (ops pages, or the viewer's own)."""

    return tuple(
        _build_account_activity_row(activity, href=href_for(activity))
        for activity in activities
    )


def _build_account_activity_row(
    activity: AccountActivity,
    *,
    href: str,
) -> AccountActivityRow:
    tone = _event_tone(activity.kind)

    return AccountActivityRow(
        name=_target_label(activity.target),
        meta=(
            f"{_event_label(activity.kind)} · "
            f"{_datetime_label(activity.occurred_at)}"
        ),
        aside=_target_meta(activity.target),
        href=href,
        tone=tone if tone in LINE_TONES else "",
        icon=_target_icon(activity.target),
    )


def _target_icon(target: object) -> str:
    match target:
        case Order():
            return "cart"
        case Product():
            return "lollipop"
        case InventoryBatch():
            return "inventory"
        case Customer():
            return "users"

    return ""


def _event_label(kind: AccountActivityKind) -> str:
    labels = {
        AccountActivityKind.ORDER_PLACED: _("Placed order"),
        AccountActivityKind.ORDER_PACKED: _("Packed order"),
        AccountActivityKind.ORDER_DELIVERED: _("Delivered order"),
        AccountActivityKind.ORDER_CANCELLED: _("Cancelled order"),
        AccountActivityKind.ORDER_EDITED: _("Edited order"),
        AccountActivityKind.PRODUCT_CREATED: _("Created product"),
        AccountActivityKind.PRODUCT_EDITED: _("Edited product"),
        AccountActivityKind.PRODUCT_ACTIVATED: _("Activated product"),
        AccountActivityKind.PRODUCT_DEACTIVATED: _("Deactivated product"),
        AccountActivityKind.INVENTORY_ADDED: _("Added batch"),
        AccountActivityKind.INVENTORY_EDITED: _("Edited batch"),
        AccountActivityKind.INVENTORY_CLOSED: _("Closed batch"),
        AccountActivityKind.CUSTOMER_CREATED: _("Created customer"),
        AccountActivityKind.CUSTOMER_EDITED: _("Edited customer"),
        AccountActivityKind.CUSTOMER_ACTIVATED: _("Activated customer"),
        AccountActivityKind.CUSTOMER_DEACTIVATED: _("Deactivated customer"),
    }

    return labels[kind]


def _event_tone(kind: AccountActivityKind) -> str:
    tones = {
        AccountActivityKind.ORDER_PLACED: "warning",
        AccountActivityKind.ORDER_PACKED: "info",
        AccountActivityKind.ORDER_DELIVERED: "success",
        AccountActivityKind.ORDER_CANCELLED: "danger",
        AccountActivityKind.ORDER_EDITED: "neutral",
        AccountActivityKind.PRODUCT_CREATED: "success",
        AccountActivityKind.PRODUCT_EDITED: "neutral",
        AccountActivityKind.PRODUCT_ACTIVATED: "success",
        AccountActivityKind.PRODUCT_DEACTIVATED: "muted",
        AccountActivityKind.INVENTORY_ADDED: "success",
        AccountActivityKind.INVENTORY_EDITED: "neutral",
        AccountActivityKind.INVENTORY_CLOSED: "muted",
        AccountActivityKind.CUSTOMER_CREATED: "success",
        AccountActivityKind.CUSTOMER_EDITED: "neutral",
        AccountActivityKind.CUSTOMER_ACTIVATED: "success",
        AccountActivityKind.CUSTOMER_DEACTIVATED: "muted",
    }

    return tones[kind]


def _target_label(target: object) -> str:
    match target:
        case Order():
            return _("Order #%(order_id)s") % {
                "order_id": target.pk,
            }

        case Product():
            return target.display_name

        case InventoryBatch():
            return target.batch_id

        case Customer():
            return target.name

    return ""


def _target_meta(target: object) -> str:
    match target:
        case Order():
            return target.customer_name

        case Product():
            return target.code_label

        case InventoryBatch():
            return target.product.display_name

        case Customer():
            return target.email

    return ""


def _datetime_label(value: datetime) -> str:
    return timezone.localtime(value).strftime(
        "%Y-%m-%d %H:%M"
    )
