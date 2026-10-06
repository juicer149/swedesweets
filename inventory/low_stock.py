from __future__ import annotations

from typing import Protocol

LOW_STOCK_THRESHOLD = 6
# At or under this (under ten) stock is running low: worth watching, not
# yet low. Lists and product pages colour it orange.
RUNNING_LOW_THRESHOLD = 9


class StockAvailabilityRow(Protocol):
    available_quantity: int


def is_low_stock(
    *,
    available_quantity: int,
    threshold: int = LOW_STOCK_THRESHOLD,
) -> bool:
    return available_quantity <= threshold
