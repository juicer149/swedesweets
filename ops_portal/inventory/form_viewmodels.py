from __future__ import annotations

from dataclasses import dataclass

from common.page_tabs import PageTab
from inventory.models import InventoryBatch
from ops_portal.inventory.forms import (
    BatchEditForm,
    BatchForm,
)
from ops_portal.inventory.presentation import batch_status_icon
from ops_portal.inventory.pricing_forms import (
    BatchPricingForm,
)

BATCH_FORM_TABS = (
    PageTab(
        key="batch",
        label="Batch",
        icon="inventory",
        template="ops_portal/inventory/includes/form_tab_batch.html",
    ),
    PageTab(
        key="pricing",
        label="Pricing",
        icon="tag",
        template="ops_portal/inventory/includes/form_tab_pricing.html",
    ),
)


@dataclass(frozen=True)
class BatchFormContext:
    form: BatchForm | BatchEditForm
    pricing_form: BatchPricingForm
    title: str
    description: str
    submit_label: str
    cancel_url: str
    batch: InventoryBatch | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "form": self.form,
            "pricing_form": self.pricing_form,
            "batch": self.batch,
            "status_icon": (
                batch_status_icon(self.batch) if self.batch else ""
            ),
            "page_tabs": BATCH_FORM_TABS,
            "tabs_label": "Batch form sections",
            "title": self.title,
            "description": self.description,
            "submit_label": self.submit_label,
            "cancel_url": self.cancel_url,
        }


@dataclass(frozen=True)
class CloseBatchContext:
    batch: InventoryBatch
    title: str
    description: str
    submit_label: str
    cancel_url: str

    def as_dict(self) -> dict[str, object]:
        return {
            "batch": self.batch,
            "status_icon": batch_status_icon(self.batch),
            "quantity_label": self.batch.product.stock_quantity_label(
                self.batch.quantity
            ),
            "title": self.title,
            "description": self.description,
            "submit_label": self.submit_label,
            "cancel_url": self.cancel_url,
        }


def build_create_batch_form_context(
    *,
    form: BatchForm,
    pricing_form: BatchPricingForm,
    cancel_url: str,
) -> BatchFormContext:
    return BatchFormContext(
        form=form,
        pricing_form=pricing_form,
        title="Add batch",
        description="",
        submit_label="Add batch",
        cancel_url=cancel_url,
    )


def build_edit_batch_form_context(
    *,
    batch: InventoryBatch,
    form: BatchEditForm,
    pricing_form: BatchPricingForm,
    cancel_url: str,
) -> BatchFormContext:
    return BatchFormContext(
        form=form,
        pricing_form=pricing_form,
        batch=batch,
        title=f"Edit batch {batch.batch_id}",
        description=(
            "Correct physical stock, location or best-before date. "
            "Product and batch ID are kept fixed for traceability."
        ),
        submit_label="Update batch",
        cancel_url=cancel_url,
    )


def build_close_batch_form_context(
    *,
    batch: InventoryBatch,
    cancel_url: str,
) -> CloseBatchContext:
    return CloseBatchContext(
        batch=batch,
        title=f"Close batch {batch.batch_id}",
        description="",
        submit_label="Close batch",
        cancel_url=cancel_url,
    )
