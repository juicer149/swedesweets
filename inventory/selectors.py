"""
Inventory read selectors.

Selectors are read-only query functions. They should not change model state,
create objects, or perform business workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum

from django.db.models import (
    Case,
    Count,
    IntegerField,
    QuerySet,
    Sum,
    Value,
    When,
)
from django.utils import timezone

from common.table_tools import normalize_sort
from inventory.expiry import (
    EXPIRY_SOON_DAYS,
    ExpiryInfo,
    build_expiry_info,
    orderable_best_before_cutoff,
)
from inventory.models import InventoryBatch
from products.models import Product

DEFAULT_BATCH_SORT = "status"

BATCH_SORTS: dict[str, tuple[str, ...]] = {
    "batch": ("batch_id",),
    "-batch": ("-batch_id",),
    "product": (
        "product__internal_number",
        "product__brand",
        "product__name",
        "batch_id",
    ),
    "-product": (
        "-product__internal_number",
        "-product__brand",
        "-product__name",
        "batch_id",
    ),
    "best_before": (
        "best_before",
        "batch_id",
    ),
    "-best_before": (
        "-best_before",
        "-batch_id",
    ),
    "quantity": (
        "quantity",
        "batch_id",
    ),
    "-quantity": (
        "-quantity",
        "-batch_id",
    ),
    "status": (
        "status_rank",
        "best_before",
        "batch_id",
    ),
    "-status": (
        "-status_rank",
        "-best_before",
        "-batch_id",
    ),
    "location": (
        "location",
        "batch_id",
    ),
    "-location": (
        "-location",
        "-batch_id",
    ),
}


# Sorting by best before or quantity is looking for stock to use: closed
# batches (no longer stock) would only be in the way. They still show
# under the default sort, and whenever the list is filtered to them.
SORTS_WITHOUT_CLOSED_BATCHES = frozenset(
    {
        "best_before",
        "-best_before",
        "quantity",
        "-quantity",
    }
)


@dataclass(frozen=True)
class BatchListRow:
    batch: InventoryBatch
    expiry: ExpiryInfo


@dataclass(frozen=True)
class PhysicalStockRow:
    product: Product
    quantity: int
    batch_count: int

    @property
    def product_id(self) -> int:
        return self.product.id

    @property
    def sku(self) -> str:
        return self.product.sku

    @property
    def internal_number_sort(self) -> int:
        return (
            self.product.internal_number
            or 999_999
        )

    @property
    def code_label(self) -> str:
        return self.product.code_label

    @property
    def catalog_label(self) -> str:
        return self.product.catalog_label

    @property
    def product_name(self) -> str:
        return self.product.display_name

    @property
    def brand(self) -> str:
        return self.product.brand


@dataclass(frozen=True)
class _PhysicalStockTotals:
    physical_quantity: int
    batch_count: int


def list_batch_rows(
    *,
    status: str | None = None,
    sort: str | None = None,
    today: date | None = None,
) -> list[BatchListRow]:
    today = today or timezone.localdate()

    return _build_batch_rows(
        batches=list_batches(
            status=status,
            sort=sort,
        ),
        today=today,
    )


def list_batches(
    *,
    status: str | None = None,
    sort: str | None = None,
) -> QuerySet[InventoryBatch]:
    normalized_sort = normalize_sort(
        sort,
        allowed_sorts=BATCH_SORTS,
        default_sort=DEFAULT_BATCH_SORT,
    )

    batches = (
        InventoryBatch.objects
        .select_related("product")
        .annotate(
            status_rank=_batch_status_rank_expression()
        )
    )

    if status in InventoryBatch.Status.values:
        batches = batches.filter(
            status=status,
        )
    elif normalized_sort in SORTS_WITHOUT_CLOSED_BATCHES:
        batches = batches.exclude(
            status=InventoryBatch.Status.CLOSED,
        )

    return batches.order_by(
        *BATCH_SORTS[normalized_sort]
    )


def physical_quantity_by_product() -> list[PhysicalStockRow]:
    stock_totals_by_product_id = (
        _physical_stock_totals_by_product_id()
    )
    products_by_id = _products_by_id(
        stock_totals_by_product_id.keys()
    )

    rows = [
        PhysicalStockRow(
            product=product,
            quantity=(
                stock_totals_by_product_id[
                    product_id
                ].physical_quantity
            ),
            batch_count=(
                stock_totals_by_product_id[
                    product_id
                ].batch_count
            ),
        )
        for product_id, product in products_by_id.items()
    ]

    return sorted(
        rows,
        key=lambda row: row.product.catalog_sort_key,
    )


def physical_quantity_by_variant(
    *,
    product: Product,
) -> dict[int, int]:
    """Stock on the shelf (active batches) of each of a product's variants,
    by variant id; a variant with none is left out."""

    rows = (
        InventoryBatch.objects
        .filter(
            product=product,
            status=InventoryBatch.Status.ACTIVE,
            quantity__gt=0,
        )
        .values("variant_id")
        .annotate(total_quantity=Sum("quantity"))
    )

    return {
        row["variant_id"]: row["total_quantity"] or 0
        for row in rows
    }


def list_available_batches_for_product(
    *,
    product: Product,
) -> QuerySet[InventoryBatch]:
    return (
        InventoryBatch.objects
        .filter(
            product=product,
            status=InventoryBatch.Status.ACTIVE,
            quantity__gt=0,
        )
        .select_related("product")
        .order_by(
            "best_before",
            "batch_id",
        )
    )


def list_orderable_batches(
    *,
    today: date | None = None,
) -> QuerySet[InventoryBatch]:
    """Return physical batches eligible for normal order reservation."""

    today = today or timezone.localdate()
    cutoff_date = orderable_best_before_cutoff(
        today=today,
    )

    return (
        InventoryBatch.objects
        .filter(
            status=InventoryBatch.Status.ACTIVE,
            quantity__gt=0,
            best_before__gt=cutoff_date,
        )
        .select_related("product")
        .order_by(
            "best_before",
            "batch_id",
        )
    )


def list_orderable_batches_for_product(
    *,
    product: Product,
    today: date | None = None,
) -> QuerySet[InventoryBatch]:
    """Return orderable physical batches for one product."""

    return list_orderable_batches(
        today=today,
    ).filter(
        product=product,
    )


def list_available_batches() -> QuerySet[InventoryBatch]:
    return (
        InventoryBatch.objects
        .filter(
            status=InventoryBatch.Status.ACTIVE,
            quantity__gt=0,
        )
        .select_related("product")
        .order_by(
            "product__internal_number",
            "product__brand",
            "product__name",
            "best_before",
            "batch_id",
        )
    )


def list_depleted_batches() -> QuerySet[InventoryBatch]:
    return (
        InventoryBatch.objects
        .filter(
            status=InventoryBatch.Status.DEPLETED,
        )
        .select_related("product")
        .order_by(
            "product__internal_number",
            "product__brand",
            "product__name",
            "batch_id",
        )
    )


def list_expiring_batch_rows_for_dashboard(
    *,
    limit: int = 3,
    days: int = EXPIRY_SOON_DAYS,
    today: date | None = None,
) -> list[BatchListRow]:
    return list_expiring_batch_rows(
        days=days,
        today=today,
    )[:limit]


def list_expiring_batch_rows(
    *,
    days: int = EXPIRY_SOON_DAYS,
    today: date | None = None,
) -> list[BatchListRow]:
    today = today or timezone.localdate()
    cutoff_date = today + timedelta(
        days=days,
    )

    batches = (
        InventoryBatch.objects
        .filter(
            status=InventoryBatch.Status.ACTIVE,
            quantity__gt=0,
            best_before__gte=today,
            best_before__lte=cutoff_date,
        )
        .select_related("product")
        .order_by(
            "best_before",
            "batch_id",
        )
    )

    return _build_batch_rows(
        batches=batches,
        today=today,
    )


def count_expiring_batches(
    *,
    days: int = EXPIRY_SOON_DAYS,
    today: date | None = None,
) -> int:
    today = today or timezone.localdate()
    cutoff_date = today + timedelta(
        days=days,
    )

    return (
        InventoryBatch.objects
        .filter(
            status=InventoryBatch.Status.ACTIVE,
            quantity__gt=0,
            best_before__gte=today,
            best_before__lte=cutoff_date,
        )
        .count()
    )


class InventoryActivityKind(StrEnum):
    ADDED = "added"
    EDITED = "edited"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class InventoryActivity:
    occurred_at: datetime
    kind: InventoryActivityKind
    batch: InventoryBatch


_INVENTORY_ACTIVITY_SPECS = (
    (
        "created_by",
        "created_at",
        InventoryActivityKind.ADDED,
    ),
    (
        "edited_by",
        "edited_at",
        InventoryActivityKind.EDITED,
    ),
    (
        "closed_by",
        "closed_at",
        InventoryActivityKind.CLOSED,
    ),
)


def list_inventory_activity_for_actor(
    *,
    actor,
    limit: int,
) -> tuple[InventoryActivity, ...]:
    activities: list[InventoryActivity] = []

    for actor_field, occurred_at_field, kind in _INVENTORY_ACTIVITY_SPECS:
        batches = (
            InventoryBatch.objects
            .filter(
                **{
                    actor_field: actor,
                    f"{occurred_at_field}__isnull": False,
                }
            )
            .select_related("product")
            .order_by(f"-{occurred_at_field}")[:limit]
        )

        activities.extend(
            InventoryActivity(
                occurred_at=getattr(
                    batch,
                    occurred_at_field,
                ),
                kind=kind,
                batch=batch,
            )
            for batch in batches
        )

    return tuple(
        sorted(
            activities,
            key=lambda activity: activity.occurred_at,
            reverse=True,
        )[:limit]
    )


def _build_batch_rows(
    *,
    batches: QuerySet[InventoryBatch],
    today: date,
) -> list[BatchListRow]:
    return [
        BatchListRow(
            batch=batch,
            expiry=build_expiry_info(
                best_before=batch.best_before,
                today=today,
            ),
        )
        for batch in batches
    ]


def _batch_status_rank_expression() -> Case:
    return Case(
        When(
            status=InventoryBatch.Status.ACTIVE,
            then=Value(1),
        ),
        When(
            status=InventoryBatch.Status.DEPLETED,
            then=Value(2),
        ),
        When(
            status=InventoryBatch.Status.CLOSED,
            then=Value(3),
        ),
        default=Value(99),
        output_field=IntegerField(),
    )


def _physical_stock_totals_by_product_id(
) -> dict[int, _PhysicalStockTotals]:
    rows = (
        InventoryBatch.objects
        .filter(
            status=InventoryBatch.Status.ACTIVE,
            quantity__gt=0,
        )
        .values("product_id")
        .annotate(
            total_quantity=Sum("quantity"),
            batch_count=Count("id"),
        )
    )

    return {
        row["product_id"]: _PhysicalStockTotals(
            physical_quantity=(
                row["total_quantity"] or 0
            ),
            batch_count=(
                row["batch_count"] or 0
            ),
        )
        for row in rows
    }


def _products_by_id(
    product_ids,
) -> dict[int, Product]:
    products = Product.objects.filter(
        id__in=product_ids,
    )

    return {
        product.id: product
        for product in products
    }
