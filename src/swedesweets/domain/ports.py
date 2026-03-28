from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from .orders import FulfilledOrder, RequestedOrder


class Clock(Protocol):
    def now(self) -> datetime: ...


class RequestedOrderRepository(Protocol):
    def get(self, requested_order_id: UUID) -> RequestedOrder: ...
    def save(self, order: RequestedOrder) -> None: ...


class FulfilledOrderRepository(Protocol):
    def get_by_requested(self, requested_order_id: UUID) -> FulfilledOrder | None: ...
    def save(self, order: FulfilledOrder) -> None: ...


class UnitOfWork(Protocol):
    def commit(self) -> None: ...
