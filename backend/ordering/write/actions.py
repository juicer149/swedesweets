from django.db import transaction

from accounts.models import Store
from catalog.models import Product

from ..domain import (
    InvalidProductSelection,
    Quantity,
    ensure_order_has_lines,
    ensure_store_is_active,
    ensure_unique_product_ids,
)
from ..models import Order, OrderItem
from .commands import PlaceOrderCommand, PlaceOrderResult


def place_order(command: PlaceOrderCommand) -> PlaceOrderResult:
    store = Store.objects.get(pk=command.store_id)

    ensure_store_is_active(is_active=store.is_active)
    ensure_order_has_lines(command.lines)
    ensure_unique_product_ids(line.product_id for line in command.lines)

    validated_quantities = {
        line.product_id: Quantity(line.quantity)
        for line in command.lines
    }

    selected_products = Product.objects.filter(
        id__in=validated_quantities.keys(),
        is_active=True,
    )

    products_by_id = {product.id: product for product in selected_products}

    if len(products_by_id) != len(validated_quantities):
        raise InvalidProductSelection(
            "One or more selected products do not exist or are inactive."
        )

    with transaction.atomic():
        order = Order.objects.create(
            store=store,
            status=Order.Status.PENDING,
        )

        items = []
        for line in command.lines:
            product = products_by_id[line.product_id]
            quantity = validated_quantities[line.product_id]

            items.append(
                OrderItem(
                    order=order,
                    product_code=product.code,
                    product_name=product.name,
                    quantity=quantity.value,
                )
            )

        OrderItem.objects.bulk_create(items)

    return PlaceOrderResult(
        order_id=str(order.id),
        line_count=len(items),
    )
