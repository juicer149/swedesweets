from __future__ import annotations

from common.ui import UiCard, UiCardRow, UiText
from ops_portal.products.presentation import product_status_presentation
from products.models import Product


def build_product_mini_card(
    *,
    product: Product,
    product_href: str,
) -> UiCard:
    """Build a compact product relation card.

    Use this when the surrounding page already gives the context, for example
    batch detail where the question is: which product does this batch belong to?
    """

    status = product_status_presentation(product)

    return UiCard(
        tone=status.tone,
        css_class="mobile-card mobile-card--relation mobile-card--product-mini",
        href=product_href,
        aria_label=f"View product {product.display_name}",
        footer_hint="Open product →",
        rows=(
            UiCardRow(
                left=UiText(
                    text=product.code_label,
                    css_class="ui-card-id",
                ),
                right=UiText(
                    text=product.weight_label,
                    css_class="ui-card-meta",
                ),
            ),
            UiCardRow(
                left=UiText(
                    text=product.display_name,
                    css_class="ui-card-title",
                ),
            ),
        ),
    )
