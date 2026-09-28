"""Delivered-order demand summaries by product."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from django.db.models import Count, Max, Sum

from orders.models import Order, OrderLine
from products.models import Product


@dataclass(frozen=True)
class ProductDeliveredDemandSummary:
    delivered_order_count: int
    delivered_quantity: int
    average_quantity_per_delivered_order: Decimal
    last_delivered_at: datetime | None

    @classmethod
    def empty(cls) -> ProductDeliveredDemandSummary:
        return cls(
            delivered_order_count=0,
            delivered_quantity=0,
            average_quantity_per_delivered_order=Decimal("0.0"),
            last_delivered_at=None,
        )


def get_product_delivered_demand_summary(
    *,
    product: Product,
) -> ProductDeliveredDemandSummary:
    stats = OrderLine.objects.filter(
        product=product,
        order__status=Order.Status.DELIVERED,
    ).aggregate(
        delivered_order_count=Count(
            "order_id",
            distinct=True,
        ),
        delivered_quantity=Sum(
            "quantity_in_units",
        ),
        last_delivered_at=Max(
            "order__delivered_at",
        ),
    )

    delivered_order_count = (
        stats["delivered_order_count"]
        or 0
    )
    delivered_quantity = (
        stats["delivered_quantity"]
        or 0
    )

    if delivered_order_count == 0:
        average = Decimal("0.0")
    else:
        average = (
            Decimal(delivered_quantity)
            / Decimal(delivered_order_count)
        ).quantize(
            Decimal("0.1")
        )

    return ProductDeliveredDemandSummary(
        delivered_order_count=delivered_order_count,
        delivered_quantity=delivered_quantity,
        average_quantity_per_delivered_order=average,
        last_delivered_at=stats["last_delivered_at"],
    )
