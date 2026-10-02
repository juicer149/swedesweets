"""Reservation-adjusted inventory availability reads."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date

from django.db.models import Sum

from common.table_tools import normalize_sort
from inventory.low_stock import (
    LOW_STOCK_THRESHOLD,
    is_low_stock,
)
from inventory.selectors import (
    list_available_batches,
    list_orderable_batches,
    physical_quantity_by_product,
)
from products.models import Product
from reservations.selectors import (
    active_reserved_quantities_by_batch_pk,
)

DEFAULT_PRODUCT_STOCK_SORT = "product"

PRODUCT_STOCK_SORTS: dict[str, tuple[str, ...]] = {
    "product": (
        "internal_number_sort",
        "brand",
        "product_name",
    ),
    "-product": (
        "-internal_number_sort",
        "-brand",
        "-product_name",
    ),
    "batches": (
        "batch_count",
        "internal_number_sort",
        "product_name",
    ),
    "-batches": (
        "-batch_count",
        "internal_number_sort",
        "product_name",
    ),
    "unit": (
        "stock_unit_sort",
        "internal_number_sort",
        "product_name",
    ),
    "-unit": (
        "-stock_unit_sort",
        "internal_number_sort",
        "product_name",
    ),
    "physical": (
        "physical_quantity",
        "internal_number_sort",
        "product_name",
    ),
    "-physical": (
        "-physical_quantity",
        "internal_number_sort",
        "product_name",
    ),
    "reserved": (
        "reserved_quantity",
        "internal_number_sort",
        "product_name",
    ),
    "-reserved": (
        "-reserved_quantity",
        "internal_number_sort",
        "product_name",
    ),
    "available": (
        "available_quantity",
        "internal_number_sort",
        "product_name",
    ),
    "-available": (
        "-available_quantity",
        "internal_number_sort",
        "product_name",
    ),
}


@dataclass(frozen=True)
class AvailableStockRow:
    product: Product
    batch_count: int
    physical_quantity: int
    reserved_quantity: int
    available_quantity: int

    @property
    def product_id(self) -> int:
        return self.product.id

    @property
    def sku(self) -> str:
        return self.product.sku

    @property
    def internal_number_sort(self) -> int:
        return self.product.internal_number or 999_999

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

    @property
    def stock_unit_sort(self) -> int:
        return self.product.stock_unit


type ProductStockSortKey = Callable[
    [AvailableStockRow],
    tuple[object, ...],
]


def available_quantity_by_product() -> list[AvailableStockRow]:
    physical_rows = physical_quantity_by_product()

    reserved_by_product_id = (
        _reserved_quantities_by_product_for_batches(
            batches=list(
                list_available_batches()
                .values_list(
                    "id",
                    "product_id",
                )
            )
        )
    )

    rows = [
        AvailableStockRow(
            product=row.product,
            batch_count=row.batch_count,
            physical_quantity=row.quantity,
            reserved_quantity=(
                reserved_by_product_id.get(
                    row.product_id,
                    0,
                )
            ),
            available_quantity=max(
                row.quantity
                - reserved_by_product_id.get(
                    row.product_id,
                    0,
                ),
                0,
            ),
        )
        for row in physical_rows
    ]

    return sorted(
        rows,
        key=lambda row: row.product.catalog_sort_key,
    )


def available_quantity_by_product_id() -> dict[int, int]:
    return {
        row.product_id: row.available_quantity
        for row in available_quantity_by_product()
    }


def sort_available_stock_rows(
    *,
    rows: list[AvailableStockRow],
    sort: str | None,
) -> list[AvailableStockRow]:
    normalized_sort = normalize_sort(
        sort,
        allowed_sorts=PRODUCT_STOCK_SORTS,
        default_sort=DEFAULT_PRODUCT_STOCK_SORT,
    )

    reverse_sort = normalized_sort.startswith("-")
    sort_key = normalized_sort.lstrip("-")

    key_function = (
        _product_stock_sort_key_functions()[
            sort_key
        ]
    )

    return sorted(
        rows,
        key=key_function,
        reverse=reverse_sort,
    )


def list_low_stock_products(
    *,
    threshold: int = LOW_STOCK_THRESHOLD,
) -> list[AvailableStockRow]:
    rows = [
        row
        for row in available_quantity_by_product()
        if is_low_stock(
            available_quantity=row.available_quantity,
            threshold=threshold,
        )
    ]

    return sorted(
        rows,
        key=lambda row: (
            row.available_quantity,
            row.product.catalog_sort_key,
        ),
    )


def list_low_stock_products_for_dashboard(
    *,
    threshold: int = LOW_STOCK_THRESHOLD,
    limit: int = 3,
) -> list[AvailableStockRow]:
    return list_low_stock_products(
        threshold=threshold,
    )[:limit]


def count_low_stock_products(
    *,
    threshold: int = LOW_STOCK_THRESHOLD,
) -> int:
    return len(
        list_low_stock_products(
            threshold=threshold,
        )
    )


def orderable_quantity_by_product_id(
    *,
    today: date | None = None,
) -> dict[int, int]:
    batches = list_orderable_batches(
        today=today,
    )

    physical_quantity_by_product_id = {
        row["product_id"]: (
            row["total_quantity"] or 0
        )
        for row in (
            batches
            .order_by()
            .values("product_id")
            .annotate(
                total_quantity=Sum("quantity"),
            )
        )
    }

    reserved_quantity_by_product_id = (
        _reserved_quantities_by_product_for_batches(
            batches=list(
                batches
                .order_by()
                .values_list(
                    "id",
                    "product_id",
                )
            )
        )
    )

    return {
        product_id: max(
            physical_quantity
            - reserved_quantity_by_product_id.get(
                product_id,
                0,
            ),
            0,
        )
        for product_id, physical_quantity
        in physical_quantity_by_product_id.items()
    }


def orderable_quantity_by_batch_pk(
    *,
    batch_pks: Iterable[int],
    today: date | None = None,
) -> dict[int, int]:
    requested_batch_pks = tuple(
        dict.fromkeys(
            int(batch_pk)
            for batch_pk in batch_pks
        )
    )

    if not requested_batch_pks:
        return {}

    physical_quantity_by_batch_pk = {
        row["id"]: row["quantity"]
        for row in (
            list_orderable_batches(
                today=today,
            )
            .filter(
                pk__in=requested_batch_pks,
            )
            .order_by()
            .values(
                "id",
                "quantity",
            )
        )
    }

    reserved_quantity_by_batch_pk = (
        active_reserved_quantities_by_batch_pk(
            batch_pks=(
                physical_quantity_by_batch_pk.keys()
            ),
        )
    )

    return {
        batch_pk: max(
            physical_quantity_by_batch_pk.get(
                batch_pk,
                0,
            )
            - reserved_quantity_by_batch_pk.get(
                batch_pk,
                0,
            ),
            0,
        )
        for batch_pk in requested_batch_pks
    }


def _reserved_quantities_by_product_for_batches(
    *,
    batches: list[tuple[int, int]],
) -> dict[int, int]:
    if not batches:
        return {}

    reserved_by_batch_pk = (
        active_reserved_quantities_by_batch_pk(
            batch_pks=[
                batch_pk
                for batch_pk, _ in batches
            ],
        )
    )

    totals: dict[int, int] = defaultdict(int)

    for batch_pk, product_id in batches:
        totals[product_id] += (
            reserved_by_batch_pk.get(
                batch_pk,
                0,
            )
        )

    return dict(totals)


def _product_stock_sort_key_functions(
) -> dict[str, ProductStockSortKey]:
    return {
        "product": lambda row: (
            row.internal_number_sort,
            row.brand.casefold(),
            row.product_name.casefold(),
        ),
        "batches": lambda row: (
            row.batch_count,
            row.internal_number_sort,
            row.product_name.casefold(),
        ),
        "unit": lambda row: (
            row.stock_unit_sort,
            row.internal_number_sort,
            row.product_name.casefold(),
        ),
        "physical": lambda row: (
            row.physical_quantity,
            row.internal_number_sort,
            row.product_name.casefold(),
        ),
        "reserved": lambda row: (
            row.reserved_quantity,
            row.internal_number_sort,
            row.product_name.casefold(),
        ),
        "available": lambda row: (
            row.available_quantity,
            row.internal_number_sort,
            row.product_name.casefold(),
        ),
    }
