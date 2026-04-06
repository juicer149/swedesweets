from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class PlaceOrderLine:
    """
    One requested product line in the write command.

    `boxes` is the number of boxes ordered for the product.
    """

    product_id: int
    boxes: int


@dataclass(frozen=True, slots=True)
class PlaceOrderCommand:
    """
    Write command for placing one order for one store.
    """

    store_id: int
    lines: tuple[PlaceOrderLine, ...]


@dataclass(frozen=True, slots=True)
class PlaceOrderResult:
    """
    Minimal result returned after successful order placement.
    """

    order_id: str
    line_count: int


@dataclass(frozen=True, slots=True)
class OrderFormRow:
    """
    Read/render row used by the order form.

    `entered_boxes` preserves raw user input so the form can be re-rendered
    after validation errors without losing what the user typed.
    """

    product_id: int
    product_code: int
    product_name: str
    category_name: str | None
    entered_boxes: str


@dataclass(frozen=True, slots=True)
class ParsedOrderForm:
    """
    Parsed and validated representation of the submitted order form.

    This is not a Django Form; it is an explicit immutable form-state object
    tailored to the ordering matrix UI.
    """

    rows: tuple[OrderFormRow, ...]
    lines: tuple[PlaceOrderLine, ...]
    errors: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def to_command(self, *, store_id: int) -> PlaceOrderCommand:
        return PlaceOrderCommand(
            store_id=store_id,
            lines=self.lines,
        )

    def add_error(self, message: str) -> "ParsedOrderForm":
        return replace(self, errors=(*self.errors, message))
