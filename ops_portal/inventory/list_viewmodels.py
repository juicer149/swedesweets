from __future__ import annotations

from dataclasses import dataclass

from django.urls import reverse

from accounts.roles import RoleSpec
from common.page_header import PageHeader, PageHeaderAction
from common.table_controls import QuickJumpOption, QuickJumpSearch
from common.ui import (
    QuantityInfo,
    StatusPresentation,
    build_quantity_info,
)
from inventory.low_stock import LOW_STOCK_THRESHOLD, RUNNING_LOW_THRESHOLD
from inventory.models import InventoryBatch
from inventory.selectors import (
    BatchListRow,
    ExpiryInfo,
)
from ops_portal.inventory.access import can_create_batch
from ops_portal.inventory.presentation import (
    batch_quantity_label,
    batch_status_icon,
    batch_status_presentation,
    product_available_quantity_label,
    product_physical_quantity_label,
    product_reserved_quantity_label,
    product_stock_status_presentation,
)
from reservations.availability import AvailableStockRow


@dataclass(frozen=True, slots=True)
class InventoryViewLink:
    key: str
    label: str
    href: str
    is_active: bool


@dataclass(frozen=True, slots=True)
class BatchPageRow:
    batch: InventoryBatch
    expiry: ExpiryInfo
    status: StatusPresentation
    quantity: QuantityInfo
    quantity_label: str
    detail_href: str

    @property
    def meta(self) -> str:
        """Phones: batch id · best before · location under the product."""

        parts = [
            self.batch.batch_id,
            f"Best before {self.batch.best_before:%Y-%m-%d}",
            self.batch.location,
        ]
        return " · ".join(part for part in parts if part)

    @property
    def icon(self) -> str:
        return batch_status_icon(self.batch)


@dataclass(frozen=True, slots=True)
class ProductStockPageRow:
    product_id: int
    product_href: str
    code_label: str
    product_label: str
    catalog_label: str
    product_name: str
    brand: str
    stock_unit_label: str
    batch_count: int
    physical_quantity: int
    physical_quantity_label: str
    reserved_quantity: int
    reserved_quantity_label: str
    available_quantity: int
    available_quantity_label: str
    available_quantity_info: QuantityInfo
    status: StatusPresentation

    @property
    def meta(self) -> str:
        """Phones: batches · reserved under the product."""

        batches = "batch" if self.batch_count == 1 else "batches"
        return (
            f"{self.batch_count} {batches} · "
            f"{self.reserved_quantity_label} reserved"
        )


def build_inventory_page_header(*, role_spec: RoleSpec) -> PageHeader:
    return PageHeader(
        title="Inventory",
        title_id="inventory-title",
        action=_build_add_batch_header_action(role_spec=role_spec),
    )


def build_inventory_view_links(
    *,
    active_view: str,
    batches_href: str,
    products_href: str,
) -> tuple[InventoryViewLink, ...]:
    return (
        InventoryViewLink(
            key="batches",
            label="Batches",
            href=batches_href,
            is_active=active_view == "batches",
        ),
        InventoryViewLink(
            key="products",
            label="Product stock",
            href=products_href,
            is_active=active_view == "products",
        ),
    )


def build_batch_page_rows(rows: list[BatchListRow]) -> list[BatchPageRow]:
    return [_build_batch_page_row(row) for row in rows]


def _build_batch_page_row(row: BatchListRow) -> BatchPageRow:
    status = batch_status_presentation(row.batch)
    quantity = build_quantity_info(
        quantity=row.batch.quantity,
        low_threshold=LOW_STOCK_THRESHOLD,
        running_low_threshold=RUNNING_LOW_THRESHOLD,
    )
    quantity_text = batch_quantity_label(row.batch)
    detail_href = _batch_detail_href(row.batch)

    return BatchPageRow(
        batch=row.batch,
        expiry=row.expiry,
        status=status,
        quantity=quantity,
        quantity_label=quantity_text,
        detail_href=detail_href,
    )


def build_product_stock_page_rows(
    rows: list[AvailableStockRow],
) -> list[ProductStockPageRow]:
    return [_build_product_stock_page_row(row) for row in rows]


def _build_product_stock_page_row(row: AvailableStockRow) -> ProductStockPageRow:
    status = product_stock_status_presentation(row)
    product_href = reverse("ops_products:detail", kwargs={"product_pk": row.product_id})
    available_quantity_info = build_quantity_info(
        quantity=row.available_quantity,
        low_threshold=LOW_STOCK_THRESHOLD,
        running_low_threshold=RUNNING_LOW_THRESHOLD,
    )

    return ProductStockPageRow(
        product_id=row.product_id,
        product_href=product_href,
        code_label=row.code_label,
        product_label=_product_stock_product_label(row),
        catalog_label=row.catalog_label,
        product_name=row.product_name,
        brand=row.brand,
        stock_unit_label=row.product.stock_unit_singular,
        batch_count=row.batch_count,
        physical_quantity=row.physical_quantity,
        physical_quantity_label=product_physical_quantity_label(row),
        reserved_quantity=row.reserved_quantity,
        reserved_quantity_label=product_reserved_quantity_label(row),
        available_quantity=row.available_quantity,
        available_quantity_label=product_available_quantity_label(row),
        available_quantity_info=available_quantity_info,
        status=status,
    )


def build_batch_quick_jump_search(
    rows: list[BatchPageRow],
) -> QuickJumpSearch:
    return QuickJumpSearch(
        title="Find batch",
        title_id="inventory-batch-search-title",
        select_id="inventory-batch-search",
        placeholder="Search batch, product or location",
        aria_label="Search inventory batches",
        options=[
            QuickJumpOption(
                label=_batch_quick_jump_label(row),
                url=row.detail_href,
            )
            for row in rows
        ],
    )


def build_product_stock_quick_jump_search(
    rows: list[ProductStockPageRow],
) -> QuickJumpSearch:
    return QuickJumpSearch(
        title="Find product stock",
        title_id="inventory-product-stock-search-title",
        select_id="inventory-product-stock-search",
        placeholder="Search product stock",
        aria_label="Search product stock",
        options=[
            QuickJumpOption(
                label=_product_stock_quick_jump_label(row),
                url=row.product_href,
            )
            for row in rows
        ],
    )


def _build_add_batch_header_action(
    *,
    role_spec: RoleSpec,
) -> PageHeaderAction | None:
    if not can_create_batch(role_spec=role_spec):
        return None

    return PageHeaderAction(
        label="Add batch",
        href=reverse("ops_inventory:create"),
        aria_label="Add a new batch",
    )


def _batch_quick_jump_label(row: BatchPageRow) -> str:
    return (
        f"{row.batch.batch_id} · "
        f"{row.batch.product.code_label} · "
        f"{row.batch.product.display_name}"
    )


def _product_stock_quick_jump_label(row: ProductStockPageRow) -> str:
    return f"{row.code_label} · {row.product_name}"


def _product_stock_product_label(row: AvailableStockRow) -> str:
    return f"{row.code_label} · {row.product.display_name} · {row.product.weight_label}"






def _batch_detail_href(batch: InventoryBatch) -> str:
    return reverse("ops_inventory:detail", kwargs={"batch_pk": batch.pk})
