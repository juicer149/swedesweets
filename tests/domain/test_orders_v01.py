from datetime import datetime, timezone
from uuid import uuid4

import pytest

from swedesweets.domain.diff import diff_requested_vs_fulfilled
from swedesweets.domain.errors import RelationshipError, ValidationError
from swedesweets.domain.services import (
    create_requested_order,
    fulfill_requested_order,
    mark_delivered,
)


def test_create_requested_order_normalizes_duplicates():
    p = uuid4()
    requested = create_requested_order(
        requested_order_id=uuid4(),
        store_id=uuid4(),
        created_at=datetime(2026, 3, 24, 10, 0, tzinfo=timezone.utc),
        items=[(p, 2), (p, 3)],
    )
    assert len(requested.items) == 1
    assert requested.items[0].quantity.value == 5


def test_fulfilled_order_diff_missing_item():
    p1, p2 = uuid4(), uuid4()
    requested = create_requested_order(
        requested_order_id=uuid4(),
        store_id=uuid4(),
        created_at=datetime(2026, 3, 24, 10, 0, tzinfo=timezone.utc),
        items=[(p1, 2), (p2, 1)],
    )
    fulfilled = fulfill_requested_order(
        fulfilled_order_id=uuid4(),
        requested=requested,
        packed_at=datetime(2026, 3, 24, 11, 0, tzinfo=timezone.utc),
        items=[(p1, 2)],
        packing_notes="p2 out of stock",
    )
    diffs = diff_requested_vs_fulfilled(requested, fulfilled)
    assert len(diffs) == 1
    assert diffs[0].requested_qty == 1
    assert diffs[0].fulfilled_qty == 0
    assert diffs[0].is_missing is True


def test_diff_requires_relationship():
    requested = create_requested_order(
        requested_order_id=uuid4(),
        store_id=uuid4(),
        created_at=datetime(2026, 3, 24, 10, 0, tzinfo=timezone.utc),
        items=[(uuid4(), 1)],
    )
    other_requested = create_requested_order(
        requested_order_id=uuid4(),
        store_id=uuid4(),
        created_at=datetime(2026, 3, 24, 10, 0, tzinfo=timezone.utc),
        items=[(uuid4(), 1)],
    )
    fulfilled = fulfill_requested_order(
        fulfilled_order_id=uuid4(),
        requested=other_requested,
        packed_at=datetime(2026, 3, 24, 11, 0, tzinfo=timezone.utc),
        items=[(uuid4(), 1)],
    )
    with pytest.raises(RelationshipError):
        diff_requested_vs_fulfilled(requested, fulfilled)


def test_mark_delivered():
    requested = create_requested_order(
        requested_order_id=uuid4(),
        store_id=uuid4(),
        created_at=datetime(2026, 3, 24, 10, 0, tzinfo=timezone.utc),
        items=[(uuid4(), 1)],
    )
    fulfilled = fulfill_requested_order(
        fulfilled_order_id=uuid4(),
        requested=requested,
        packed_at=datetime(2026, 3, 24, 11, 0, tzinfo=timezone.utc),
        items=[(requested.items[0].product_id.value, 1)],
    )
    delivered = mark_delivered(
        fulfilled=fulfilled,
        delivered_at=datetime(2026, 3, 24, 12, 0, tzinfo=timezone.utc),
    )
    assert delivered.is_delivered is True


def test_quantity_validation():
    with pytest.raises(ValidationError):
        create_requested_order(
            requested_order_id=uuid4(),
            store_id=uuid4(),
            created_at=datetime(2026, 3, 24, 10, 0, tzinfo=timezone.utc),
            items=[(uuid4(), 0)],
        )
