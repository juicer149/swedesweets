from collections.abc import Iterable, Sequence

from ..models import Order
from .errors import (
    DuplicateProduct,
    EmptyOrder,
    InvalidOrderStatusTransition,
    StoreInactive,
)


def ensure_store_is_active(*, is_active: bool) -> None:
    if not is_active:
        raise StoreInactive("Inactive stores cannot place orders.")


def ensure_order_has_lines(lines: Sequence[object]) -> None:
    if len(lines) == 0:
        raise EmptyOrder("Order must contain at least one line.")


def ensure_unique_product_ids(product_ids: Iterable[int]) -> None:
    seen: set[int] = set()

    for product_id in product_ids:
        if product_id in seen:
            raise DuplicateProduct(
                f"Product {product_id} appears more than once in the same order."
            )
        seen.add(product_id)


def ensure_can_mark_packed(*, current_status: str) -> None:
    """
    Allow packing only from pending or packed.

    - pending -> packed: valid
    - packed -> packed: tolerated
    - delivered -> packed: invalid
    - cancelled -> packed: invalid
    """
    if current_status == Order.Status.DELIVERED:
        raise InvalidOrderStatusTransition(
            "Delivered orders cannot be marked as packed."
        )

    if current_status == Order.Status.CANCELLED:
        raise InvalidOrderStatusTransition(
            "Cancelled orders cannot be marked as packed."
        )


def ensure_can_mark_delivered(*, current_status: str) -> None:
    """
    Allow delivery from pending, packed, or delivered.

    - pending -> delivered: allowed for MVP bypass flow
    - packed -> delivered: valid
    - delivered -> delivered: tolerated
    - cancelled -> delivered: invalid
    """
    if current_status == Order.Status.CANCELLED:
        raise InvalidOrderStatusTransition(
            "Cancelled orders cannot be marked as delivered."
        )


def ensure_can_cancel(*, current_status: str) -> None:
    """
    Allow cancellation from pending, packed, or cancelled.

    - pending -> cancelled: valid
    - packed -> cancelled: valid
    - cancelled -> cancelled: tolerated
    - delivered -> cancelled: invalid
    """
    if current_status == Order.Status.DELIVERED:
        raise InvalidOrderStatusTransition(
            "Delivered orders cannot be cancelled."
        )
