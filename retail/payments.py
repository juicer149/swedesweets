from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum

from django.utils import timezone

from payments.contracts import (
    HostedPaymentError,
    HostedPaymentProvider,
)
from payments.models import PaymentAttempt
from payments.providers.factory import (
    get_default_hosted_payment_provider,
)
from payments.services import (
    PaymentReconciliationConflict,
    attach_provider_payment_id,
    create_hosted_payment_session,
    payment_reference,
    reconcile_payment_attempt,
)
from retail.models import RetailCheckoutSession
from retail.services import (
    cancel_retail_payment,
    complete_retail_payment,
    fail_retail_payment,
    start_retail_payment,
)

__all__ = [
    "PaymentReconciliationConflict",
    "UNCONFIRMED_ATTEMPT_GRACE",
    "RetailPaymentRecovery",
    "RetailPaymentRecoveryAction",
    "RetailPaymentRedirect",
    "begin_retail_hosted_payment",
    "cancel_open_retail_payment",
    "is_past_unconfirmed_grace",
    "reconcile_retail_payment",
    "recover_retail_payment",
    "resolve_unconfirmed_retail_payment",
    "retry_retail_hosted_payment",
]

logger = logging.getLogger(__name__)

# How long an attempt without a provider payment id is left alone before
# it is resolved automatically. Resolving earlier could race a provider
# call that is still in flight.
UNCONFIRMED_ATTEMPT_GRACE = timedelta(minutes=2)


class RetailPaymentRecoveryAction(StrEnum):
    CONTINUE_PAYMENT = "continue_payment"
    CONFIRMED = "confirmed"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_CANCELLED = "payment_cancelled"
    NEEDS_SUPPORT = "needs_support"


@dataclass(frozen=True, slots=True)
class RetailPaymentRedirect:
    attempt: PaymentAttempt
    redirect_url: str


@dataclass(frozen=True, slots=True)
class RetailPaymentRecovery:
    attempt: PaymentAttempt
    action: RetailPaymentRecoveryAction
    redirect_url: str | None = None


def begin_retail_hosted_payment(
    *,
    checkout: RetailCheckoutSession,
    customer_return_url: str,
    webhook_url: str,
) -> RetailPaymentRedirect:
    """Start a retail payment and create its external hosted checkout.

    The provider is resolved before any local attempt exists, so a
    misconfigured provider never leaves a pending attempt behind.
    """

    provider = get_default_hosted_payment_provider()

    attempt = start_retail_payment(
        checkout=checkout,
    )

    return _create_retail_hosted_payment_session(
        attempt=attempt,
        provider=provider,
        customer_return_url=customer_return_url,
        webhook_url=webhook_url,
    )


def retry_retail_hosted_payment(
    *,
    attempt: PaymentAttempt,
    customer_return_url: str,
    webhook_url: str,
) -> RetailPaymentRedirect:
    """Retry provider initialization for the same local attempt."""

    return _create_retail_hosted_payment_session(
        attempt=attempt,
        provider=get_default_hosted_payment_provider(),
        customer_return_url=customer_return_url,
        webhook_url=webhook_url,
    )


def is_past_unconfirmed_grace(
    attempt: PaymentAttempt,
) -> bool:
    return timezone.now() - attempt.created_at >= UNCONFIRMED_ATTEMPT_GRACE


def resolve_unconfirmed_retail_payment(
    *,
    attempt: PaymentAttempt,
    provider: HostedPaymentProvider | None = None,
) -> PaymentAttempt:
    """Settle a pending attempt whose provider payment id never arrived.

    The provider is searched by our reference. If it has no payment, none
    was created and the attempt is cancelled, releasing the buyer's cart.
    If it has one, the attempt is linked to it and reconciled normally.
    """

    provider = provider or get_default_hosted_payment_provider()

    attempt = PaymentAttempt.objects.get(
        pk=attempt.pk,
    )

    if (
        attempt.status != PaymentAttempt.Status.PENDING
        or attempt.provider_payment_id
    ):
        return attempt

    external = provider.find_payment_by_reference(
        reference=payment_reference(attempt),
    )

    if external is None:
        return cancel_retail_payment(
            attempt=attempt,
        )

    attach_provider_payment_id(
        attempt=attempt,
        provider_payment_id=external.provider_payment_id,
    )

    return reconcile_payment_attempt(
        attempt=attempt,
        provider=provider,
        on_succeeded=complete_retail_payment,
        on_failed=fail_retail_payment,
    ).attempt


def cancel_open_retail_payment(
    *,
    attempt: PaymentAttempt,
) -> RetailPaymentRecovery:
    """Cancel a pending retail payment at the buyer's request.

    The provider checkout is deactivated first and its state read back
    afterwards. If the buyer managed to pay in the meantime, the payment
    wins and the order is placed instead of cancelled.

    Raises HostedPaymentError when the provider cannot be reached to
    resolve an attempt that never received a provider payment id.
    """

    provider = get_default_hosted_payment_provider()

    attempt = PaymentAttempt.objects.get(
        pk=attempt.pk,
    )

    if attempt.status != PaymentAttempt.Status.PENDING:
        return _recovery_for_settled_attempt(attempt)

    if not attempt.provider_payment_id:
        attempt = resolve_unconfirmed_retail_payment(
            attempt=attempt,
            provider=provider,
        )

        if attempt.status != PaymentAttempt.Status.PENDING:
            return _recovery_for_settled_attempt(attempt)

    deactivated = True

    try:
        provider.cancel_payment(
            provider_payment_id=attempt.provider_payment_id,
        )
    except HostedPaymentError:
        deactivated = False

        logger.warning(
            "Provider refused to cancel payment attempt %s.",
            attempt.pk,
            exc_info=True,
        )

    try:
        attempt = reconcile_payment_attempt(
            attempt=attempt,
            provider=provider,
            on_succeeded=complete_retail_payment,
            on_failed=fail_retail_payment,
        ).attempt
    except (
        HostedPaymentError,
        PaymentReconciliationConflict,
    ):
        logger.warning(
            "Could not read back payment attempt %s after cancelling.",
            attempt.pk,
            exc_info=True,
        )

        attempt.refresh_from_db()

    if attempt.status != PaymentAttempt.Status.PENDING:
        return _recovery_for_settled_attempt(attempt)

    if deactivated:
        return RetailPaymentRecovery(
            attempt=cancel_retail_payment(
                attempt=attempt,
            ),
            action=RetailPaymentRecoveryAction.PAYMENT_CANCELLED,
        )

    return RetailPaymentRecovery(
        attempt=attempt,
        action=RetailPaymentRecoveryAction.NEEDS_SUPPORT,
    )


def recover_retail_payment(
    *,
    attempt: PaymentAttempt,
) -> RetailPaymentRecovery:
    """Resolve the customer-facing state of one retail payment.

    Recovery never guesses about unknown external payment creation. A
    pending attempt without a provider payment id is left alone during a
    short grace period, then resolved by searching the provider for our
    reference instead of creating another external checkout.
    """

    attempt = (
        PaymentAttempt.objects
        .select_related("order")
        .get(pk=attempt.pk)
    )

    if attempt.status == PaymentAttempt.Status.SUCCEEDED:
        return RetailPaymentRecovery(
            attempt=attempt,
            action=RetailPaymentRecoveryAction.CONFIRMED,
        )

    if attempt.status == PaymentAttempt.Status.FAILED:
        return RetailPaymentRecovery(
            attempt=attempt,
            action=RetailPaymentRecoveryAction.PAYMENT_FAILED,
        )

    if (
        attempt.status == PaymentAttempt.Status.CANCELLED
        and not attempt.provider_payment_id
    ):
        return RetailPaymentRecovery(
            attempt=attempt,
            action=RetailPaymentRecoveryAction.PAYMENT_FAILED,
        )

    if not attempt.provider_payment_id:
        if not is_past_unconfirmed_grace(attempt):
            return RetailPaymentRecovery(
                attempt=attempt,
                action=RetailPaymentRecoveryAction.NEEDS_SUPPORT,
            )

        try:
            attempt = resolve_unconfirmed_retail_payment(
                attempt=attempt,
            )
        except Exception:
            logger.warning(
                "Could not resolve unconfirmed payment attempt %s.",
                attempt.pk,
                exc_info=True,
            )

            attempt.refresh_from_db()

            return RetailPaymentRecovery(
                attempt=attempt,
                action=RetailPaymentRecoveryAction.NEEDS_SUPPORT,
            )

        if attempt.status != PaymentAttempt.Status.PENDING:
            return RetailPaymentRecovery(
                attempt=attempt,
                action=(
                    RetailPaymentRecoveryAction.CONFIRMED
                    if attempt.status == PaymentAttempt.Status.SUCCEEDED
                    else RetailPaymentRecoveryAction.PAYMENT_FAILED
                ),
            )

    try:
        provider = get_default_hosted_payment_provider()

        result = reconcile_payment_attempt(
            attempt=attempt,
            provider=provider,
            on_succeeded=complete_retail_payment,
            on_failed=fail_retail_payment,
        )
    except Exception:
        attempt.refresh_from_db()

        return RetailPaymentRecovery(
            attempt=attempt,
            action=RetailPaymentRecoveryAction.NEEDS_SUPPORT,
        )

    reconciled = result.attempt
    external = result.external

    redirect_url: str | None = None

    match reconciled.status:
        case PaymentAttempt.Status.SUCCEEDED:
            action = RetailPaymentRecoveryAction.CONFIRMED

        case PaymentAttempt.Status.FAILED | PaymentAttempt.Status.CANCELLED:
            action = RetailPaymentRecoveryAction.PAYMENT_FAILED

        case (
            PaymentAttempt.Status.PENDING
        ) if external.hosted_payment_url:
            action = RetailPaymentRecoveryAction.CONTINUE_PAYMENT
            redirect_url = external.hosted_payment_url

        case _:
            action = RetailPaymentRecoveryAction.NEEDS_SUPPORT

    return RetailPaymentRecovery(
        attempt=reconciled,
        action=action,
        redirect_url=redirect_url,
    )


def reconcile_retail_payment(
    *,
    attempt: PaymentAttempt,
) -> PaymentAttempt:
    """Reconcile one retail payment attempt against provider truth.

    Terminal outcomes are retail's own: a successful payment places the
    retail order, a failed payment releases its temporary reservations.
    """

    provider = get_default_hosted_payment_provider()

    result = reconcile_payment_attempt(
        attempt=attempt,
        provider=provider,
        on_succeeded=complete_retail_payment,
        on_failed=fail_retail_payment,
    )

    return result.attempt


def _recovery_for_settled_attempt(
    attempt: PaymentAttempt,
) -> RetailPaymentRecovery:
    if attempt.status == PaymentAttempt.Status.SUCCEEDED:
        action = RetailPaymentRecoveryAction.CONFIRMED
    elif attempt.status in {
        PaymentAttempt.Status.FAILED,
        PaymentAttempt.Status.CANCELLED,
    }:
        action = RetailPaymentRecoveryAction.PAYMENT_CANCELLED
    else:
        action = RetailPaymentRecoveryAction.NEEDS_SUPPORT

    return RetailPaymentRecovery(
        attempt=attempt,
        action=action,
    )


def _create_retail_hosted_payment_session(
    *,
    attempt: PaymentAttempt,
    provider: HostedPaymentProvider,
    customer_return_url: str,
    webhook_url: str,
) -> RetailPaymentRedirect:
    session = create_hosted_payment_session(
        attempt=attempt,
        provider=provider,
        customer_return_url=customer_return_url,
        webhook_url=webhook_url,
    )

    attempt.refresh_from_db()

    return RetailPaymentRedirect(
        attempt=attempt,
        redirect_url=session.redirect_url,
    )
