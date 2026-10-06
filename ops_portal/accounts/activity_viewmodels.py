from __future__ import annotations

from django.urls import reverse

from accounts.activity import AccountActivity
from accounts.activity_viewmodels import (
    AccountActivityRow,
    build_account_activity_rows,
)
from customers.models import Customer
from inventory.models import InventoryBatch
from orders.models import Order
from products.models import Product


def build_ops_account_activity_rows(
    activities: tuple[AccountActivity, ...],
) -> tuple[AccountActivityRow, ...]:
    return build_account_activity_rows(
        activities,
        href_for=lambda activity: _target_href(activity.target),
    )


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
