from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict
from uuid import UUID

from .orders import FulfilledOrder, RequestedOrder
from .ports import Clock, FulfilledOrderRepository, RequestedOrderRepository, UnitOfWork


@dataclass
class FixedClock(Clock):
    current: datetime

    def now(self) -> datetime:
        return self.current


class NoopUnitOfWork(UnitOfWork):
    def commit(self) -> None:
        return None


@dataclass
class InMemoryRequestedOrders(RequestedOrderRepository):
    data: Dict[UUID, RequestedOrder]

    def get(self, requested_order_id: UUID) -> RequestedOrder:
        return self.data[requested_order_id]

    def save(self, order: RequestedOrder) -> None:
        self.data[order.requested_order_id.value] = order


@dataclass
class InMemoryFulfilledOrders(FulfilledOrderRepository):
    data: Dict[UUID, FulfilledOrder]  # keyed by requested_order_id

    def get_by_requested(self, requested_order_id: UUID) -> FulfilledOrder | None:
        return self.data.get(requested_order_id)

    def save(self, order: FulfilledOrder) -> None:
        self.data[order.requested_order_id.value] = order
