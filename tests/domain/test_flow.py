"""
Behaviour tests.

These test real-world usage of the domain.
"""

from swedesweets.domain import create_order


def test_store_can_create_order(store, products):
    p1, p2 = products[:2]

    order = create_order(
        store_id=store.id,
        requested_items=[
            (p1.id, 2),
            (p2.id, 3),
        ],
    )

    assert len(order.items) == 2
    assert order.items[0].quantity.value == 2
    assert order.items[1].quantity.value == 3


def test_order_quantities_are_preserved(store, products):
    product = products[0]

    order = create_order(
        store_id=store.id,
        requested_items=[(product.id, 5)],
    )

    assert order.items[0].quantity.value == 5
