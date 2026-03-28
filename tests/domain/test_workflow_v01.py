from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from swedesweets.domain.diff import diff_requested_vs_fulfilled
from swedesweets.domain.services import (
    create_requested_order,
    fulfill_requested_order,
    mark_delivered,
)


@dataclass(frozen=True)
class Scenario:
    store_id: UUID
    requested_order_id: UUID
    fulfilled_order_id: UUID
    created_at: datetime
    packed_at: datetime
    delivered_at: datetime
    p1: UUID
    p2: UUID
    p3: UUID


@pytest.fixture()
def scenario() -> Scenario:
    return Scenario(
        store_id=uuid4(),
        requested_order_id=uuid4(),
        fulfilled_order_id=uuid4(),
        created_at=datetime(2026, 3, 24, 9, 0, tzinfo=timezone.utc),
        packed_at=datetime(2026, 3, 24, 10, 0, tzinfo=timezone.utc),
        delivered_at=datetime(2026, 3, 24, 12, 0, tzinfo=timezone.utc),
        p1=uuid4(),
        p2=uuid4(),
        p3=uuid4(),
    )


def test_workflow_happy_path_no_diff(scenario: Scenario) -> None:
    requested = create_requested_order(
        requested_order_id=scenario.requested_order_id,
        store_id=scenario.store_id,
        created_at=scenario.created_at,
        items=[(scenario.p1, 2), (scenario.p2, 1), (scenario.p3, 5)],
    )

    fulfilled = fulfill_requested_order(
        fulfilled_order_id=scenario.fulfilled_order_id,
        requested=requested,
        packed_at=scenario.packed_at,
        items=[(scenario.p1, 2), (scenario.p2, 1), (scenario.p3, 5)],
        packing_notes="",
    )

    delivered = mark_delivered(fulfilled=fulfilled, delivered_at=scenario.delivered_at)

    assert delivered.is_delivered is True
    assert diff_requested_vs_fulfilled(requested, delivered) == ()


def test_workflow_missing_item_creates_diff_and_notes(scenario: Scenario) -> None:
    requested = create_requested_order(
        requested_order_id=scenario.requested_order_id,
        store_id=scenario.store_id,
        created_at=scenario.created_at,
        items=[(scenario.p1, 2), (scenario.p2, 1), (scenario.p3, 5)],
    )

    # Supplier could not pack p3 at all.
    fulfilled = fulfill_requested_order(
        fulfilled_order_id=scenario.fulfilled_order_id,
        requested=requested,
        packed_at=scenario.packed_at,
        items=[(scenario.p1, 2), (scenario.p2, 1)],
        packing_notes="p3 out of stock",
    )

    diffs = diff_requested_vs_fulfilled(requested, fulfilled)
    assert len(diffs) == 1
    assert diffs[0].product_id.value == scenario.p3
    assert diffs[0].requested_qty == 5
    assert diffs[0].fulfilled_qty == 0
    assert diffs[0].is_missing is True
    assert fulfilled.packing_notes == "p3 out of stock"


def test_workflow_extra_item_creates_diff(scenario: Scenario) -> None:
    requested = create_requested_order(
        requested_order_id=scenario.requested_order_id,
        store_id=scenario.store_id,
        created_at=scenario.created_at,
        items=[(scenario.p1, 2), (scenario.p2, 1)],
    )

    # Supplier packed one extra p2 for whatever reason.
    fulfilled = fulfill_requested_order(
        fulfilled_order_id=scenario.fulfilled_order_id,
        requested=requested,
        packed_at=scenario.packed_at,
        items=[(scenario.p1, 2), (scenario.p2, 2)],
    )

    diffs = diff_requested_vs_fulfilled(requested, fulfilled)
    assert len(diffs) == 1
    assert diffs[0].product_id.value == scenario.p2
    assert diffs[0].requested_qty == 1
    assert diffs[0].fulfilled_qty == 2
    assert diffs[0].is_extra is True


def test_workflow_duplicate_lines_are_normalized(scenario: Scenario) -> None:
    requested = create_requested_order(
        requested_order_id=scenario.requested_order_id,
        store_id=scenario.store_id,
        created_at=scenario.created_at,
        items=[(scenario.p1, 1), (scenario.p1, 1)],  # duplicates
    )
    assert requested.items[0].quantity.value == 2
