from __future__ import annotations

from common.ui import (
    TONE_DANGER,
    TONE_MUTED,
    TONE_SUCCESS,
    TONE_WARNING,
    StatusPresentation,
    UiText,
)
from inventory.models import InventoryBatch
from reservations.availability import AvailableStockRow

INVENTORY_STATUS_ACTIVE = StatusPresentation(
    value=InventoryBatch.Status.ACTIVE,
    label="Active",
    tone=TONE_SUCCESS,
    text=UiText(
        text="Active",
        css_class="status-text status-text--success",
    ),
)

INVENTORY_STATUS_DEPLETED = StatusPresentation(
    value=InventoryBatch.Status.DEPLETED,
    label="Depleted",
    tone=TONE_WARNING,
    text=UiText(
        text="Depleted",
        css_class="status-text status-text--warning",
    ),
)

INVENTORY_STATUS_CLOSED = StatusPresentation(
    value=InventoryBatch.Status.CLOSED,
    label="Closed",
    tone=TONE_MUTED,
    text=UiText(
        text="Closed",
        css_class="status-text status-text--muted",
    ),
)

PRODUCT_STOCK_STATUS_AVAILABLE = StatusPresentation(
    value="available",
    label="Available",
    tone=TONE_SUCCESS,
    text=UiText(
        text="Available",
        css_class="status-text status-text--success",
    ),
)

PRODUCT_STOCK_STATUS_RESERVED = StatusPresentation(
    value="reserved",
    label="Reserved",
    tone=TONE_WARNING,
    text=UiText(
        text="Reserved",
        css_class="status-text status-text--warning",
    ),
)

PRODUCT_STOCK_STATUS_OUT = StatusPresentation(
    value="out",
    label="Out",
    tone=TONE_DANGER,
    text=UiText(
        text="Out",
        css_class="status-text status-text--danger",
    ),
)


def batch_status_presentation(batch: InventoryBatch) -> StatusPresentation:
    match batch.status:
        case InventoryBatch.Status.ACTIVE:
            return INVENTORY_STATUS_ACTIVE
        case InventoryBatch.Status.DEPLETED:
            return INVENTORY_STATUS_DEPLETED
        case _:
            return INVENTORY_STATUS_CLOSED


def product_stock_status_presentation(
    row: AvailableStockRow,
) -> StatusPresentation:
    if row.available_quantity > 0:
        return PRODUCT_STOCK_STATUS_AVAILABLE

    if row.reserved_quantity > 0:
        return PRODUCT_STOCK_STATUS_RESERVED

    return PRODUCT_STOCK_STATUS_OUT


def batch_status_icon(batch: InventoryBatch) -> str:
    match batch.status:
        case InventoryBatch.Status.ACTIVE:
            return "box"
        case InventoryBatch.Status.DEPLETED:
            return "packed"
        case _:
            return "x"


def batch_quantity_label(batch: InventoryBatch) -> str:
    return f"{batch.product.stock_quantity_label(batch.quantity)}"


def quantity_label(*, product, quantity: int) -> str:
    return product.stock_quantity_label(quantity)


def product_physical_quantity_label(row: AvailableStockRow) -> str:
    return f"{row.product.stock_quantity_label(row.physical_quantity)}"


def product_reserved_quantity_label(row: AvailableStockRow) -> str:
    return f"{row.product.stock_quantity_label(row.reserved_quantity)}"


def product_available_quantity_label(row: AvailableStockRow) -> str:
    return f"{row.product.stock_quantity_label(row.available_quantity)}"
