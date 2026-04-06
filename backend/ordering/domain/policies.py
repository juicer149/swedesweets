from collections.abc import Iterable, Sequence

from .errors import DuplicateProduct, EmptyOrder, StoreInactive


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
