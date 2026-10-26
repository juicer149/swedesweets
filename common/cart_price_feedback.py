"""Presentation of a confirmed change, without parsing currency labels."""
from decimal import Decimal


def cart_price_feedback(before: Decimal | None, after: Decimal | None) -> dict:
    delta = after - before if before is not None and after is not None else None
    return {
        "subtotal_label": f"€{after:.2f}" if after is not None else None,
        "subtotal_delta_label": (
            ("+" if delta > 0 else "−") + f"€{abs(delta):.2f}" if delta else None
        ),
    }
