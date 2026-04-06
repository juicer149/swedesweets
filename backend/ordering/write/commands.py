from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class PlaceOrderLine:
    product_id: int
    quantity: int


@dataclass(frozen=True, slots=True)
class PlaceOrderCommand:
    store_id: int
    lines: tuple[PlaceOrderLine, ...]


@dataclass(frozen=True, slots=True)
class PlaceOrderResult:
    order_id: str
    line_count: int


@dataclass(frozen=True, slots=True)
class OrderFormRow:
    product_id: int
    product_code: int
    product_name: str
    category_name: str | None
    entered_quantity: str


@dataclass(frozen=True, slots=True)
class ParsedOrderForm:
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
