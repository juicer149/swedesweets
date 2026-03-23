#! src/swedesweets/domain/policies.py
"""
Business policies.

Purpose:
- Centralize business rules
- Avoid duplication across services
- Keep rules configurable and explicit

Design:
- Keep simple for MVP
- Promote reuse via small functions instead of scattered constants
"""

from .errors import BusinessRuleError

MAX_ORDER_QTY = 15
ORDER_EDIT_CUTOFF_HOURS = 24


def enforce_max_quantity(qty: int) -> None:
    """Enforce maximum allowed quantity per product.

    Why:
    - Prevent unrealistic or accidental large orders
    - Centralize one rule used in multiple flows
    """
    if qty > MAX_ORDER_QTY:
        raise BusinessRuleError(
            f"quantity {qty} exceeds max {MAX_ORDER_QTY}"
        )
