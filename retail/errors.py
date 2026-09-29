"""RETAIL application failures.

Kept separate from services so actor-facing code can catch retail
failures without depending on the service layer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from retail.models import RetailCheckoutSession


class InvalidRetailCart(ValueError):
    """Raised when a retail cart use case violates a retail invariant."""


class InvalidRetailOrder(ValueError):
    """Raised when a retail checkout violates a business invariant."""


class RetailCheckoutPaymentInProgress(InvalidRetailOrder):
    """Raised when a cart already has a checkout with a pending payment.

    The caller should send the buyer to the existing checkout instead of
    starting a second payment for the same cart.
    """

    def __init__(
        self,
        *,
        checkout: RetailCheckoutSession,
    ) -> None:
        super().__init__(
            "retail cart already has a payment in progress"
        )
        self.checkout = checkout
