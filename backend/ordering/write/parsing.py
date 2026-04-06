from ..domain.value_objects import MAX_BOXES_PER_LINE
from .commands import OrderFormRow, ParsedOrderForm, PlaceOrderLine


def _make_row(product, entered_boxes: str) -> OrderFormRow:
    return OrderFormRow(
        product_id=product.id,
        product_code=product.code,
        product_name=product.name,
        category_name=product.category.name if product.category else None,
        entered_boxes=entered_boxes,
    )


def _parse_boxes(raw_value: str, product_name: str) -> tuple[int | None, tuple[str, ...]]:
    """
    Parse one raw box quantity value from the submitted form.

    Returns:
    - parsed integer if valid
    - None if the value should not produce a line
    - one or more user-facing validation errors
    """
    if raw_value == "":
        return None, ()

    try:
        boxes = int(raw_value)
    except ValueError:
        return None, (f"{product_name}: number of boxes must be a whole number.",)

    if boxes < 0:
        return None, (f"{product_name}: number of boxes cannot be negative.",)

    if boxes == 0:
        return None, ()

    if boxes > MAX_BOXES_PER_LINE:
        return None, (
            f"{product_name}: number of boxes cannot exceed {MAX_BOXES_PER_LINE}.",
        )

    return boxes, ()


def _parse_product_row(product, data) -> tuple[OrderFormRow, PlaceOrderLine | None, tuple[str, ...]]:
    """
    Parse one product row from the matrix-style order form.

    Returns:
    - row for re-rendering
    - optional line for command creation
    - row-specific validation errors
    """
    raw_value = data.get(f"qty_{product.id}", "").strip()
    row = _make_row(product, raw_value)

    boxes, errors = _parse_boxes(raw_value, product.name)
    if errors:
        return row, None, errors

    if boxes is None:
        return row, None, ()

    line = PlaceOrderLine(
        product_id=product.id,
        boxes=boxes,
    )
    return row, line, ()


def empty_order_form(products) -> ParsedOrderForm:
    """
    Build an empty render-state object for the order form.
    """
    rows = tuple(_make_row(product, "") for product in products)
    return ParsedOrderForm(rows=rows, lines=(), errors=())


def parse_order_form(products, data) -> ParsedOrderForm:
    """
    Parse the matrix-style ordering form.

    INPUT MODEL:
    - one input field per product
    - empty input means 'not ordered'
    - positive integer means 'number of boxes ordered'

    RESPONSIBILITY:
    - preserve raw entered values for re-render
    - build validated command lines
    - report user-facing input errors

    NON-RESPONSIBILITY:
    - enforce final system invariants independent of the UI
      (that remains the job of the write action and domain objects)
    """
    rows: list[OrderFormRow] = []
    lines: list[PlaceOrderLine] = []
    errors: list[str] = []
    seen_product_ids: set[int] = set()

    for product in products:
        row, line, row_errors = _parse_product_row(product, data)
        rows.append(row)
        errors.extend(row_errors)

        if line is None:
            continue

        if line.product_id in seen_product_ids:
            errors.append(f"{product.name}: duplicate product in submitted form.")
            continue

        seen_product_ids.add(line.product_id)
        lines.append(line)

    if not lines and not errors:
        errors.append(
            "Please enter a number of boxes greater than zero for at least one product."
        )

    return ParsedOrderForm(
        rows=tuple(rows),
        lines=tuple(lines),
        errors=tuple(errors),
    )
