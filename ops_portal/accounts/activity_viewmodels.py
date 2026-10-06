from __future__ import annotations

from dataclasses import dataclass

from django.urls import reverse

from accounts.activity import AccountActivity
from accounts.activity_viewmodels import build_account_activity_presentations
from customers.models import Customer
from inventory.models import InventoryBatch
from orders.models import Order
from products.models import Product

# Tones a .line__icon can show; neutral and muted events get the plain grey.
LINE_TONES = frozenset({"warning", "info", "success", "danger"})


@dataclass(frozen=True, slots=True)
class AccountActivityRow:
    """One thing the account did, as a .line--link row:
    "Order #31" / "Placed order · 2026-10-06 14:02" / Café Blanc."""

    name: str
    meta: str
    aside: str
    href: str
    tone: str
    icon: str


def build_ops_account_activity_rows(
    activities: tuple[AccountActivity, ...],
) -> tuple[AccountActivityRow, ...]:
    presentations = build_account_activity_presentations(activities)

    return tuple(
        AccountActivityRow(
            name=presentation.target_label,
            meta=f"{presentation.event_label} · {presentation.occurred_at_label}",
            aside=presentation.meta,
            href=_target_href(activity.target),
            tone=presentation.tone if presentation.tone in LINE_TONES else "",
            icon=_target_icon(activity.target),
        )
        for activity, presentation in zip(
            activities,
            presentations,
            strict=True,
        )
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


def _target_href(target: object) -> str:
    match target:
        case Order():
            return reverse(
                "ops_orders:detail",
                kwargs={
                    "order_id": target.pk,
                },
            )

        case Product():
            return reverse(
                "ops_products:detail",
                kwargs={
                    "product_pk": target.pk,
                },
            )

        case InventoryBatch():
            return reverse(
                "ops_inventory:detail",
                kwargs={
                    "batch_pk": target.pk,
                },
            )

        case Customer():
            return reverse(
                "ops_customers:detail",
                kwargs={
                    "customer_pk": target.pk,
                },
            )

    return ""
