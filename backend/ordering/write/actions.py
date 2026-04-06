from django.db import transaction

from accounts.models import Store
from catalog.models import Product

from ..domain import (
    BoxQuantity,
    InvalidProductSelection,
    ensure_order_has_lines,
    ensure_store_is_active,
    ensure_unique_product_ids,
)
from ..models import Order, OrderItem
from .commands import PlaceOrderCommand, PlaceOrderLine, PlaceOrderResult


def _get_store(store_id: int) -> Store:
    return Store.objects.get(pk=store_id)


def _validate_command(
    store: Store,
    command: PlaceOrderCommand,
) -> dict[int, BoxQuantity]:
    """
    Validate store-level and line-level invariants for the command.

    Returns a mapping of product_id -> validated BoxQuantity so later steps
    can work with already-checked domain values.
    """
    ensure_store_is_active(is_active=store.is_active)
    ensure_order_has_lines(command.lines)
    ensure_unique_product_ids(line.product_id for line in command.lines)

    return {
        line.product_id: BoxQuantity(line.boxes)
        for line in command.lines
    }


def _load_selected_products(
    validated_boxes: dict[int, BoxQuantity],
) -> dict[int, Product]:
    """
    Load orderable catalog products referenced by the command.

    Raises InvalidProductSelection if any referenced product is missing or
    not currently orderable. This prevents orders from snapshotting invalid
    catalog entries.
    """
    selected_products = Product.objects.filter(
        id__in=validated_boxes.keys(),
        is_orderable=True,
    ).select_related("category")

    products_by_id = {product.id: product for product in selected_products}

    if len(products_by_id) != len(validated_boxes):
        raise InvalidProductSelection(
            "One or more selected products do not exist or are inactive."
        )

    return products_by_id


def _build_order_items(
    *,
    order: Order,
    lines: tuple[PlaceOrderLine, ...],
    products_by_id: dict[int, Product],
    validated_boxes: dict[int, BoxQuantity],
) -> list[OrderItem]:
    """
    Build immutable historical order item snapshots.

    The returned items are not yet persisted. They snapshot catalog data
    needed to understand the order even if the catalog changes later.
    """
    items: list[OrderItem] = []

    for line in lines:
        product = products_by_id[line.product_id]
        box_quantity = validated_boxes[line.product_id]

        items.append(
            OrderItem(
                order=order,
                product_code=product.code,
                product_name=product.name,
                product_category_name=product.category.name if product.category else "",
                product_weight_grams=product.weight_grams,
                product_units_per_box=product.units_per_box,
                boxes=box_quantity.value,
            )
        )

    return items


def _create_order_with_items(
    *,
    store: Store,
    lines: tuple[PlaceOrderLine, ...],
    products_by_id: dict[int, Product],
    validated_boxes: dict[int, BoxQuantity],
) -> tuple[Order, int]:
    """
    Persist the order aggregate root and all line snapshots atomically.
    """
    with transaction.atomic():
        order = Order.objects.create(
            store=store,
            status=Order.Status.PENDING,
        )

        items = _build_order_items(
            order=order,
            lines=lines,
            products_by_id=products_by_id,
            validated_boxes=validated_boxes,
        )
        OrderItem.objects.bulk_create(items)

    return order, len(items)


def place_order(command: PlaceOrderCommand) -> PlaceOrderResult:
    """
    Execute the order placement use case.

    FLOW:
    - load store
    - validate command invariants
    - load referenced orderable products
    - create order and immutable item snapshots
    - return a small result DTO

    This function is the public write entrypoint for placing orders.
    """
    store = _get_store(command.store_id)
    validated_boxes = _validate_command(store, command)
    products_by_id = _load_selected_products(validated_boxes)
    order, line_count = _create_order_with_items(
        store=store,
        lines=command.lines,
        products_by_id=products_by_id,
        validated_boxes=validated_boxes,
    )

    return PlaceOrderResult(
        order_id=str(order.id),
        line_count=line_count,
    )
