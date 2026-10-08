from __future__ import annotations

from dataclasses import dataclass

from common.lines import LineMeta, LineView


@dataclass(frozen=True, slots=True)
class NavbarCartLine:
    """A line in the navbar's cart: read-only, like an order's line (the
    picture, the name, its grey lines, the quantity on the right), with
    only the bin; the quantity is changed on the cart's page."""

    line_id: int
    label: str
    product_url: str
    metadata: tuple[str, ...]
    quantity: int
    remove_url: str
    image_url: str | None = None

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
    empty_message: str
    empty_action_label: str
    empty_action_url: str

    @property
    def has_lines(self) -> bool:
        return self.line_count > 0
