"""What a product line shows, the same shape on every page.

Carts, reviews and order pages each have their own line data (a cart
line, an order line, a checkout line). Each turns itself into a
LineView, and one set of includes draws it:

    includes/ui/line_product.html   picture circle, name, meta lines
    includes/ui/line.html           a read-only line: product + aside

so a cart, a review and an order look alike without three templates
spelling the same markup out.
"""

from __future__ import annotations

from dataclasses import dataclass

META_PLAIN = ""
META_OFFER = "offer"  # an offer or reason: a little darker
META_TOTAL = "total"  # a line total: darker still


@dataclass(frozen=True, slots=True)
class LineMeta:
    """One grey line under the name.

    prefix is shown before the text ("Total: "). total_for marks the text
    as the live line total of that cart line (data-cart-line-total), which
    storefront-cart.js updates when the quantity changes.
    """

    text: str
    kind: str = META_PLAIN
    prefix: str = ""
    total_for: int | None = None


@dataclass(frozen=True, slots=True)
class LineView:
    name: str
    href: str | None = None
    image_url: str | None = None
    metas: tuple[LineMeta, ...] = ()
    # Short text on the right of a read-only line: a quantity or an amount.
    aside: str = ""


def metas(*items: LineMeta | None) -> tuple[LineMeta, ...]:
    """The meta lines that have text, in order."""

    return tuple(item for item in items if item is not None and item.text)


def meta(
    text: str | None,
    kind: str = META_PLAIN,
    **kwargs,
) -> LineMeta | None:
    """A meta line, or None when there is no text for it."""

    if not text:
        return None

    return LineMeta(text=str(text), kind=kind, **kwargs)
