from datetime import datetime, timezone
from uuid import uuid4

import pytest

from swedesweets.domain.adapters_memory import (
    FixedClock,
    InMemoryFulfilledOrders,
    InMemoryRequestedOrders,
    NoopUnitOfWork,
)
from swedesweets.domain.use_cases import deliver_order, pack_order, request_order


def test_use_case_full_workflow():
    clock = FixedClock(datetime(2026, 3, 24, 10, 0, tzinfo=timezone.utc))
    requested_repo = InMemoryRequestedOrders(data={})
    fulfilled_repo = InMemoryFulfilledOrders(data={})
    uow = NoopUnitOfWork()

    store_id = uuid4()
    requested_order_id = uuid4()
    fulfilled_order_id = uuid4()
    p1, p2 = uuid4(), uuid4()

    requested = request_order(
        requested_order_id=requested_order_id,
        store_id=store_id,
        items=[(p1, 2), (p2, 1)],
        clock=clock,
        requested_repo=requested_repo,
        uow=uow,
    )

    # move time forward
    clock.current = datetime(2026, 3, 24, 11, 0, tzinfo=timezone.utc)

    fulfilled = pack_order(
        fulfilled_order_id=fulfilled_order_id,
        requested_order_id=requested.requested_order_id.value,
        packed_items=[(p1, 2), (p2, 1)],
        packing_notes="",
        clock=clock,
        requested_repo=requested_repo,
        fulfilled_repo=fulfilled_repo,
        uow=uow,
    )

    assert fulfilled.is_delivered is False

    clock.current = datetime(2026, 3, 24, 12, 0, tzinfo=timezone.utc)

    delivered = deliver_order(
        requested_order_id=requested.requested_order_id.value,
        clock=clock,
        fulfilled_repo=fulfilled_repo,
        uow=uow,
    )

    assert delivered.is_delivered is True
