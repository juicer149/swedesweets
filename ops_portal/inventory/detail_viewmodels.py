from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

from accounts.roles import RoleSpec
from common.page_tabs import PageTab
from common.ui import QuantityInfo, build_quantity_info
from inventory.expiry import ExpiryInfo, build_expiry_info
from inventory.low_stock import LOW_STOCK_THRESHOLD, RUNNING_LOW_THRESHOLD
from inventory.models import InventoryBatch
from ops_portal.inventory.access import (
    can_close_batch,
    can_edit_batch,
)
from ops_portal.inventory.presentation import batch_status_icon
from pricing.models import CommercialPrice
from reservations.datatypes import BatchUsage

BATCH_DETAIL_TABS = (
    PageTab(
        key="batch",
        label="Batch",
        icon="inventory",
        template="ops_portal/inventory/includes/detail_tab_batch.html",
    ),
    PageTab(
        key="pricing",
        label="Pricing",
        icon="tag",
        template="ops_portal/inventory/includes/detail_tab_pricing.html",
    ),
    PageTab(
        key="usage",
        label="Usage",
        icon="cart",
        template="ops_portal/inventory/includes/detail_tab_usage.html",
    ),
)


@dataclass(frozen=True, slots=True)
class BatchStockSummary:
    physical_quantity: int
    physical_quantity_label: str
    reserved_quantity: int
    reserved_quantity_label: str
    available_quantity: int
    available_quantity_label: str
    is_orderable: bool

    @property
    def available_info(self) -> QuantityInfo:
        """Colour of Available: the same scale as lists and product pages."""

        return build_quantity_info(
            quantity=self.available_quantity,
            low_threshold=LOW_STOCK_THRESHOLD,
            running_low_threshold=RUNNING_LOW_THRESHOLD,
        )

    @classmethod
    def from_batch_and_allocations(
        cls,
        *,
        batch: InventoryBatch,
        allocations: list[BatchUsage],
    ) -> BatchStockSummary:
        reserved_quantity = sum(
            usage.quantity
            for usage in allocations
            if usage.is_active_reservation
        )

        available_quantity = max(
            batch.quantity - reserved_quantity,
            0,
        )

        return cls(
            physical_quantity=batch.quantity,
            physical_quantity_label=(
                batch.product.stock_quantity_label(
                    batch.quantity
                )
            ),
            reserved_quantity=reserved_quantity,
            reserved_quantity_label=(
                batch.product.stock_quantity_label(
                    reserved_quantity
                )
            ),
            available_quantity=available_quantity,
            available_quantity_label=(
                batch.product.stock_quantity_label(
                    available_quantity
                )
            ),
            is_orderable=(
                batch.status
                == InventoryBatch.Status.ACTIVE
                and batch.product.active
                and available_quantity > 0
            ),
        )


@dataclass(frozen=True, slots=True)
class BatchPriceAmountSummary:
    currency: str
    price: Decimal

    @property
    def price_label(self) -> str:
        return f"{self.price:.2f}"


@dataclass(frozen=True, slots=True)
class BatchChannelPricingSummary:
    label: str
    enabled: bool
    amounts: tuple[BatchPriceAmountSummary, ...]

    @property
    def status_label(self) -> str:
        return (
            "Active"
            if self.enabled
            else "Inactive"
        )

    @property
    def state(self) -> str:
        """Colour of the status: on (green), off (red), none (grey)."""

        if not self.amounts:
            return "none"

        return "on" if self.enabled else "off"

    @property
    def prices_label(self) -> str:
        return " · ".join(
            f"{amount.price_label} {amount.currency}"
            for amount in self.amounts
        )


@dataclass(frozen=True, slots=True)
class BatchPricingSummary:
    reason: str
    reason_label: str
    business: BatchChannelPricingSummary
    retail: BatchChannelPricingSummary

    @property
    def channels(self) -> tuple[BatchChannelPricingSummary, ...]:
        """Business, then retail: one row each on the Pricing tab."""

        return (self.business, self.retail)

    @property
    def is_configured(self) -> bool:
        return bool(
            self.business.amounts
            or self.retail.amounts
        )

    @property
    def has_active_offer(self) -> bool:
        return (
            self.business.enabled
            or self.retail.enabled
        )



@dataclass(frozen=True, slots=True)
class BatchUsageRow:
    order_id: int
    order_href: str
    customer_name: str
    customer_href: str
    quantity: int
    quantity_label: str
    allocation_status: str
    order_status: str

    @property
    def title(self) -> str:
        return f"#{self.order_id} · {self.customer_name}"

    @property
    def meta(self) -> str:
        return f"{self.allocation_status} · {self.order_status}"


@dataclass(frozen=True, slots=True)
class BatchDetailContext:
    batch: InventoryBatch
    stock: BatchStockSummary
    pricing: BatchPricingSummary
    product_href: str
    usage_rows: list[BatchUsageRow]
    usage_count: int
    expiry: ExpiryInfo
    edit_href: str | None
    close_href: str | None
    page_tabs: tuple[PageTab, ...]
    title: str
    description: str
    cancel_url: str

    def as_dict(self) -> dict[str, object]:
        return {
            "batch": self.batch,
            "stock": self.stock,
            "pricing": self.pricing,
            "product_href": self.product_href,
            "usage_rows": self.usage_rows,
            "usage_count": self.usage_count,
            "expiry": self.expiry,
            "edit_href": self.edit_href,
            "close_href": self.close_href,
            "status_icon": batch_status_icon(self.batch),
            "page_tabs": self.page_tabs,
            "tabs_label": "Batch sections",
            "back_url": self.cancel_url,
            "back_label": "Back to inventory",
            "title": self.title,
            "description": self.description,
            "cancel_url": self.cancel_url,
        }


def build_batch_detail_context(
    *,
    batch: InventoryBatch,
    allocations: list[BatchUsage],
    business_price: CommercialPrice | None,
    retail_price: CommercialPrice | None,
    cancel_url: str,
    role_spec: RoleSpec,
) -> BatchDetailContext:
    usage_rows = _build_usage_rows(
        allocations,
    )

    stock = BatchStockSummary.from_batch_and_allocations(
        batch=batch,
        allocations=allocations,
    )

    pricing = _build_batch_pricing_summary(
        business_price=business_price,
        retail_price=retail_price,
    )

    product_href = reverse(
        "ops_products:detail",
        kwargs={
            "product_pk": batch.product_id,
        },
    )

    return BatchDetailContext(
        batch=batch,
        stock=stock,
        pricing=pricing,
        product_href=product_href,
        usage_rows=usage_rows,
        usage_count=len(usage_rows),
        expiry=build_expiry_info(
            best_before=batch.best_before,
            today=timezone.localdate(),
        ),
        edit_href=(
            reverse(
                "ops_inventory:edit",
                kwargs={
                    "batch_pk": batch.pk,
                },
            )
            if can_edit_batch(
                batch=batch,
                role_spec=role_spec,
            )
            else None
        ),
        close_href=(
            reverse(
                "ops_inventory:close",
                kwargs={
                    "batch_pk": batch.pk,
                },
            )
            if can_close_batch(
                batch=batch,
                role_spec=role_spec,
            )
            else None
        ),
        page_tabs=BATCH_DETAIL_TABS,
        title=f"Batch {batch.batch_id}",
        description="",
        cancel_url=cancel_url,
    )


def _build_batch_pricing_summary(
    *,
    business_price: CommercialPrice | None,
    retail_price: CommercialPrice | None,
) -> BatchPricingSummary:
    reason = _pricing_reason(
        business_price=business_price,
        retail_price=retail_price,
    )

    return BatchPricingSummary(
        reason=reason,
        reason_label=_reason_label(
            reason
        ),
        business=_build_channel_pricing_summary(
            label="Business",
            commercial_price=business_price,
        ),
        retail=_build_channel_pricing_summary(
            label="Retail",
            commercial_price=retail_price,
        ),
    )


def _build_channel_pricing_summary(
    *,
    label: str,
    commercial_price: CommercialPrice | None,
) -> BatchChannelPricingSummary:
    if commercial_price is None:
        return BatchChannelPricingSummary(
            label=label,
            enabled=False,
            amounts=(),
        )

    amounts = tuple(
        BatchPriceAmountSummary(
            currency=amount.currency,
            price=amount.price,
        )
        for amount in commercial_price.amounts.all()
    )

    return BatchChannelPricingSummary(
        label=label,
        enabled=commercial_price.enabled,
        amounts=amounts,
    )


def _pricing_reason(
    *,
    business_price: CommercialPrice | None,
    retail_price: CommercialPrice | None,
) -> str:
    if (
        business_price is not None
        and business_price.reason
    ):
        return business_price.reason

    if (
        retail_price is not None
        and retail_price.reason
    ):
        return retail_price.reason

    return ""


def _reason_label(
    reason: str,
) -> str:
    if not reason:
        return ""

    return CommercialPrice.Reason(
        reason
    ).label


def _build_usage_rows(
    allocations: list[BatchUsage],
) -> list[BatchUsageRow]:
    rows: list[BatchUsageRow] = []

    for usage in allocations:
        order_href = reverse(
            "ops_orders:detail",
            kwargs={
                "order_id": usage.order.pk,
            },
        )

        customer_href = ""

        if usage.customer_id is not None:
            customer_href = reverse(
                "ops_customers:detail",
                kwargs={
                    "customer_pk": usage.customer_id,
                },
            )

        rows.append(
            BatchUsageRow(
                order_id=usage.order.pk,
                order_href=order_href,
                customer_name=usage.buyer_name,
                customer_href=customer_href,
                quantity=usage.quantity,
                quantity_label=usage.quantity_label,
                allocation_status=(
                    usage.allocation_status
                ),
                order_status=usage.order_status,
            )
        )

    return rows




def batch_expiry_label(
    batch: InventoryBatch,
) -> str:
    expiry = build_expiry_info(
        best_before=batch.best_before,
        today=timezone.localdate(),
    )

    return expiry.label
