from .commands import OrderFormRow, ParsedOrderForm, PlaceOrderLine


def _make_row(product, entered_quantity: str) -> OrderFormRow:
    return OrderFormRow(
        product_id=product.id,
        product_code=product.code,
        product_name=product.name,
        category_name=product.category.name if product.category else None,
        entered_quantity=entered_quantity,
    )


def empty_order_form(products) -> ParsedOrderForm:
    rows = tuple(_make_row(product, "") for product in products)
    return ParsedOrderForm(rows=rows, lines=(), errors=())


def parse_order_form(products, data) -> ParsedOrderForm:
    rows: list[OrderFormRow] = []
    lines: list[PlaceOrderLine] = []
    errors: list[str] = []
    seen_product_ids: set[int] = set()

    for product in products:
        raw_value = data.get(f"qty_{product.id}", "").strip()
        rows.append(_make_row(product, raw_value))

        if raw_value == "":
            continue

        try:
            quantity = int(raw_value)
        except ValueError:
            errors.append(f"{product.name}: quantity must be a whole number.")
            continue

        if quantity < 0:
            errors.append(f"{product.name}: quantity cannot be negative.")
            continue

        if quantity == 0:
            continue

        if product.id in seen_product_ids:
            errors.append(f"{product.name}: duplicate product in submitted form.")
            continue

        seen_product_ids.add(product.id)
        lines.append(
            PlaceOrderLine(
                product_id=product.id,
                quantity=quantity,
            )
        )

    if not lines and not errors:
        errors.append(
            "Please enter a quantity greater than zero for at least one product."
        )

    return ParsedOrderForm(
        rows=tuple(rows),
        lines=tuple(lines),
        errors=tuple(errors),
    )
