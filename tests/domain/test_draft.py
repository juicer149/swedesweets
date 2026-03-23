import pytest
from datetime import datetime, timedelta, timezone

from swedesweets.domain import create_draft, update_draft, finalize_draft
from swedesweets.domain.errors import BusinessRuleError, ValidationError


def now():
    return datetime.now(timezone.utc)


def future_delivery():
    """Safe distance from cutoff (important!)."""
    return now() + timedelta(days=2)


def test_create_empty_draft(store):
    draft = create_draft(
        store_id=store.id,
        delivery_at=future_delivery(),
    )

    assert len(draft.items) == 0


def test_update_draft_add_item(store, products):
    draft = create_draft(
        store_id=store.id,
        delivery_at=future_delivery(),
    )

    product = products[0]

    updated = update_draft(
        draft=draft,
        product_id=product.id,
        qty=3,
        current_time=now(),
    )

    assert updated.items[product.id].value == 3


def test_update_draft_remove_item_with_zero(store, products):
    draft = create_draft(
        store_id=store.id,
        delivery_at=future_delivery(),
    )

    product = products[0]

    draft = update_draft(
        draft=draft,
        product_id=product.id,
        qty=3,
        current_time=now(),
    )

    updated = update_draft(
        draft=draft,
        product_id=product.id,
        qty=0,
        current_time=now(),
    )

    assert product.id not in updated.items


def test_draft_is_immutable(store, products):
    draft = create_draft(
        store_id=store.id,
        delivery_at=future_delivery(),
    )

    product = products[0]

    updated = update_draft(
        draft=draft,
        product_id=product.id,
        qty=2,
        current_time=now(),
    )

    assert product.id not in draft.items
    assert product.id in updated.items


def test_draft_mapping_is_read_only(store):
    draft = create_draft(
        store_id=store.id,
        delivery_at=future_delivery(),
    )

    with pytest.raises(TypeError):
        draft.items["hack"] = "bad"


def test_update_draft_after_cutoff_fails(store, products):
    delivery = now() + timedelta(hours=10)

    draft = create_draft(
        store_id=store.id,
        delivery_at=delivery,
    )

    product = products[0]

    with pytest.raises(BusinessRuleError):
        update_draft(
            draft=draft,
            product_id=product.id,
            qty=1,
            current_time=now(),
        )


def test_finalize_draft_success(store, products):
    draft = create_draft(
        store_id=store.id,
        delivery_at=future_delivery(),
    )

    product = products[0]

    draft = update_draft(
        draft=draft,
        product_id=product.id,
        qty=4,
        current_time=now(),
    )

    order = finalize_draft(draft=draft)

    assert len(order.items) == 1
    assert order.items[0].quantity.value == 4


def test_finalize_empty_draft_fails(store):
    draft = create_draft(
        store_id=store.id,
        delivery_at=future_delivery(),
    )

    with pytest.raises(ValidationError):
        finalize_draft(draft=draft)


def test_finalize_after_cutoff_fails(store, products):
    delivery = now() + timedelta(hours=10)

    draft = create_draft(
        store_id=store.id,
        delivery_at=delivery,
    )

    product = products[0]

    # before cutoff
    draft = update_draft(
        draft=draft,
        product_id=product.id,
        qty=1,
        current_time=delivery - timedelta(hours=25),
    )

    # after cutoff
    with pytest.raises(BusinessRuleError):
        finalize_draft(draft=draft)
