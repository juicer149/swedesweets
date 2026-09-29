"""Local stand-in for a hosted payment provider. Development only.

Payments are kept in Django's cache and completed from a local page
with Pay/Decline buttons, so the whole checkout flow can be exercised
without provider credentials or network access.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from django.core.cache import cache
from django.urls import reverse

from payments.contracts import (
    ExternalPaymentState,
    ExternalPaymentStatus,
    HostedPaymentError,
    HostedPaymentRequest,
    HostedPaymentSession,
)

FAKE_PAYMENT_TIMEOUT_SECONDS = 24 * 60 * 60

_CACHE_PREFIX = "payments:fake:"
_REFERENCE_PREFIX = "payments:fake-ref:"


class FakePaymentError(HostedPaymentError):
    """Raised when a fake payment cannot be found or changed."""


class FakeHostedPaymentProvider:
    def create_payment(
        self,
        *,
        request: HostedPaymentRequest,
    ) -> HostedPaymentSession:
        payment_id = f"fake-{uuid4().hex}"

        cache.set(
            _cache_key(payment_id),
            {
                "status": ExternalPaymentStatus.PENDING.value,
                "reference": request.reference,
                "amount": str(request.amount),
                "currency": request.currency,
                "description": request.description,
                "customer_return_url": request.customer_return_url,
                "transaction_id": None,
            },
            FAKE_PAYMENT_TIMEOUT_SECONDS,
        )
        cache.set(
            _reference_key(request.reference),
            payment_id,
            FAKE_PAYMENT_TIMEOUT_SECONDS,
        )

        return HostedPaymentSession(
            provider_payment_id=payment_id,
            redirect_url=fake_checkout_url(payment_id),
        )

    def get_payment(
        self,
        *,
        provider_payment_id: str,
    ) -> ExternalPaymentState:
        payment = get_fake_payment(
            provider_payment_id
        )

        if payment is None:
            raise FakePaymentError(
                f"unknown fake payment {provider_payment_id}"
            )

        status = ExternalPaymentStatus(
            payment["status"]
        )

        return ExternalPaymentState(
            provider_payment_id=provider_payment_id,
            status=status,
            provider_transaction_id=payment["transaction_id"],
            hosted_payment_url=(
                fake_checkout_url(provider_payment_id)
                if status == ExternalPaymentStatus.PENDING
                else None
            ),
        )

    def find_payment_by_reference(
        self,
        *,
        reference: str,
    ) -> ExternalPaymentState | None:
        payment_id = cache.get(
            _reference_key(reference)
        )

        if payment_id is None:
            return None

        return self.get_payment(
            provider_payment_id=payment_id,
        )

    def cancel_payment(
        self,
        *,
        provider_payment_id: str,
    ) -> None:
        payment = get_fake_payment(
            provider_payment_id
        )

        if payment is None:
            raise FakePaymentError(
                f"unknown fake payment {provider_payment_id}"
            )

        if payment["status"] == ExternalPaymentStatus.SUCCEEDED.value:
            raise FakePaymentError(
                "fake payment is already paid"
            )

        if payment["status"] == ExternalPaymentStatus.PENDING.value:
            payment["status"] = ExternalPaymentStatus.FAILED.value

            cache.set(
                _cache_key(provider_payment_id),
                payment,
                FAKE_PAYMENT_TIMEOUT_SECONDS,
            )


def fake_checkout_url(
    payment_id: str,
) -> str:
    return reverse(
        "payments:fake_checkout",
        kwargs={
            "payment_id": payment_id,
        },
    )


def get_fake_payment(
    payment_id: str,
) -> dict[str, Any] | None:
    return cache.get(
        _cache_key(payment_id)
    )


def complete_fake_payment(
    payment_id: str,
    *,
    succeeded: bool,
) -> dict[str, Any] | None:
    """Move a pending fake payment to its final state.

    Completing an already finished payment leaves it unchanged, like a
    real provider would.
    """

    payment = get_fake_payment(
        payment_id
    )

    if payment is None:
        return None

    if payment["status"] == ExternalPaymentStatus.PENDING.value:
        payment["status"] = (
            ExternalPaymentStatus.SUCCEEDED.value
            if succeeded
            else ExternalPaymentStatus.FAILED.value
        )
        payment["transaction_id"] = (
            f"fake-txn-{uuid4().hex[:12]}"
            if succeeded
            else None
        )

        cache.set(
            _cache_key(payment_id),
            payment,
            FAKE_PAYMENT_TIMEOUT_SECONDS,
        )

    return payment


def _cache_key(
    payment_id: str,
) -> str:
    return f"{_CACHE_PREFIX}{payment_id}"


def _reference_key(
    reference: str,
) -> str:
    return f"{_REFERENCE_PREFIX}{reference}"
