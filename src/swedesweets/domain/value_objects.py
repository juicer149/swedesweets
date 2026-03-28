from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from .errors import ValidationError


def require_aware(dt: datetime) -> datetime:
    """
    Require timezone-aware datetime to avoid silent timezone bugs.
    Recommend using UTC everywhere.
    """
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValidationError("datetime must be timezone-aware (e.g. timezone.utc)")
    return dt


@dataclass(frozen=True)
class Quantity:
    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int):
            raise ValidationError("Quantity must be an int")
        if self.value <= 0:
            raise ValidationError("Quantity must be > 0")


@dataclass(frozen=True)
class StoreId:
    value: UUID


@dataclass(frozen=True)
class ProductId:
    value: UUID


@dataclass(frozen=True)
class OrderId:
    value: UUID
