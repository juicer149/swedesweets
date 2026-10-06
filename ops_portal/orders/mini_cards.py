from __future__ import annotations

from common.ui import UiCard, UiCardRow, UiText
from ops_portal.orders.presentation import (
    build_order_status_presentation,
    contents_summary,
    order_card_css_class,
    order_lifecycle_label,
    order_product_count,
    order_total_quantity,
)
from orders.models import Order


def build_customer_order_mini_card(
    *,
    order: Order,
    order_href: str,
) -> UiCard:
    """Build a compact order card for customer detail views."""

    status = build_order_status_presentation(order.status)

    return UiCard(
        tone=status.tone,
        css_class=order_card_css_class(order.status),
        href=order_href,
        aria_label=f"View order #{order.pk}",
        footer_hint="Open order →",
        rows=(
            _order_header_row(order=order, status=status),
            UiCardRow(
                left=UiText(
                    text=contents_summary(
                        product_count=order_product_count(order),
                        total_quantity=order_total_quantity(order),
                    ),
                    css_class="ui-card-title",
                ),
            ),
            UiCardRow(
                left=UiText(
                    text=order_lifecycle_label(order),
                    css_class="ui-card-muted",
                ),
            ),
        ),
    )


def _order_header_row(
    *,
    order: Order,
    status,
) -> UiCardRow:
    return UiCardRow(
        left=UiText(
            text=f"Order #{order.pk}",
            css_class="ui-card-id",
        ),
        right=status.text,
    )
