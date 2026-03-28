from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from .diff import ItemDiff
from .orders import FulfilledOrder, RequestedOrder


@dataclass(frozen=True)
class SupplierOrderView:
    requested: RequestedOrder
    fulfilled: FulfilledOrder | None
    diffs: tuple[ItemDiff, ...]

    @property
    def is_packed(self) -> bool:
        return self.fulfilled is not None

    @property
    def is_delivered(self) -> bool:
        return self.fulfilled is not None and self.fulfilled.is_delivered

    @property
    def has_diff(self) -> bool:
        return len(self.diffs) > 0
