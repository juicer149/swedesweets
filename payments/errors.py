"""Payment failures.

Kept separate from contracts and services so callers can catch payment
failures without depending on provider contracts or the service layer.
"""

from __future__ import annotations


class HostedPaymentError(RuntimeError):
    """Raised when a hosted payment provider cannot be trusted to have
    completed an operation.

    Provider adapters raise subclasses of this error so callers outside
    the payments package never depend on a specific provider.
    """


class HostedPaymentConfigurationError(HostedPaymentError):
    """Raised when no hosted payment provider can be built from settings."""


class InvalidPaymentAttempt(ValueError):
    """Raised when payment attempt state violates a payment invariant."""


class PaymentReconciliationConflict(RuntimeError):
    """Provider truth conflicts with an irreversible local payment state."""
