from __future__ import annotations

from dataclasses import dataclass
from datetime import date

type BatchQuantity = tuple[int, int]


@dataclass(frozen=True, slots=True)
class BatchAvailability:
    """Physical batch data required by reservation planning."""

    batch_pk: int
    batch_code: str
    product_id: int
    physical_quantity: int
    best_before: date


@dataclass(frozen=True, slots=True)
class BatchPick:
    """Planned reservation from one physical batch."""

    batch_pk: int
    quantity: int
