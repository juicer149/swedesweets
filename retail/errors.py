"""RETAIL application failures.

Kept separate from services so actor-facing code can catch retail
failures without depending on the service layer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext

if TYPE_CHECKING:
    from retail.models import RetailCheckoutSession


class InvalidRetailCart(ValueError):
    """Raised when a retail cart use case violates a retail invariant."""


class InvalidRetailOrder(ValueError):
    """Raised when a retail checkout violates a business invariant."""


class RetailCartLocked(InvalidRetailCart):
    """Raised when a cart is changed while one of its checkouts is being paid.

    The draft order sent to the payment provider is a snapshot of the cart.
    Changing the cart meanwhile would have no effect on what the buyer pays,
    so the cart stays read-only until the payment succeeds, fails or is
    cancelled.
    """

    def __init__(
        self,
        *,
        checkout: RetailCheckoutSession,
    ) -> None:
        super().__init__(
            gettext(
                "You have a payment in progress. "
                "Finish or cancel it before changing your cart."
            )
        )
        self.checkout = checkout


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
