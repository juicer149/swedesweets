from __future__ import annotations

from dataclasses import dataclass

from common.lines import LineMeta, LineView


@dataclass(frozen=True, slots=True)
class NavbarCartLine:
    """Shared cart row presentation for pages and navbar panels."""

    line_id: int
    label: str
    product_url: str
    metadata: tuple[str, ...]
    quantity: int
    remove_url: str
    image_url: str | None = None
    # Its product: the catalog's in-cart badges count from the lines.
    product_id: int | None = None
    name: str = ""
    brand: str = ""
    variant_label: str = ""
    quantity_url: str = ""
    unit_price_label: str | None = None
    line_total_label: str | None = None

    @property
    def line_view(self) -> LineView:
        return LineView(
            name=self.label,
            href=self.product_url,
            image_url=self.image_url,
            metas=tuple(LineMeta(text) for text in self.metadata if text),
            aside=f"× {self.quantity}",
        )


@dataclass(frozen=True, slots=True)
class NavbarCart:
    aria_label: str
    title: str
    line_count: int
    lines: tuple[NavbarCartLine, ...]
    fragment_url: str
    proceed_label: str
    proceed_url: str
    empty_action_label: str
    empty_action_url: str
    subtotal_label: str | None = None
    is_retail: bool = False
    payment_url: str | None = None

    @property
    def has_lines(self) -> bool:
        return self.line_count > 0
