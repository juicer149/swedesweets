"""Payment safeguards: the SumUp checkout expires with the stock hold,
slow answers become payment errors, a different charged amount is
refused, and missing keys are reported at start."""

from __future__ import annotations

import json
import socket
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.test import override_settings

from payments.checks import sumup_keys_are_set
from payments.contracts import (
    ExternalPaymentState,
    ExternalPaymentStatus,
    HostedPaymentRequest,
)
from payments.errors import PaymentReconciliationConflict
from payments.models import PaymentAttempt
from payments.providers.sumup import (
    SumUpHostedPaymentProvider,
    SumUpPaymentError,
)
from payments.services import _require_matching_amount


def _provider() -> SumUpHostedPaymentProvider:
    return SumUpHostedPaymentProvider(
        api_key="test-key",
        merchant_code="M123456",
    )


class _Response:
    def __init__(self, payload: dict) -> None:
        self._body = json.dumps(payload).encode()

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        return None


def test_sumup_checkout_expires_when_the_hold_ends():
    expires_at = datetime(2026, 10, 9, 14, 30, tzinfo=UTC)

    with patch(
        "payments.providers.sumup.urlopen",
        return_value=_Response(
            {
                "id": "c-1",
                "hosted_checkout_url": "https://checkout.sumup.com/pay/c-1",
            }
        ),
    ) as mocked:
        _provider().create_payment(
            request=HostedPaymentRequest(
                reference="payment-1",
                amount=Decimal("25.00"),
                currency="EUR",
                description="SwedeSweets order 1",
                customer_return_url="https://shop.example.com/return",
                webhook_url="https://shop.example.com/webhook",
                expires_at=expires_at,
            )
        )

    payload = json.loads(mocked.call_args.args[0].data)

    assert payload["valid_until"] == "2026-10-09T14:30:00+00:00"


@pytest.mark.parametrize(
    "error",
    [socket.timeout("timed out"), ConnectionResetError("reset")],
)
def test_sumup_slow_or_dropped_answer_is_a_payment_error(error):
    with patch(
        "payments.providers.sumup.urlopen",
        side_effect=error,
    ), pytest.raises(SumUpPaymentError):
        _provider().get_payment(provider_payment_id="c-1")


def test_sumup_reports_the_charged_amount():
    with patch(
        "payments.providers.sumup.urlopen",
        return_value=_Response(
            {
                "id": "c-1",
                "status": "PAID",
                "transaction_id": "tx-1",
                "amount": 25.0,
                "currency": "EUR",
            }
        ),
    ):
        state = _provider().get_payment(provider_payment_id="c-1")

    assert state.amount == Decimal("25")
    assert state.currency == "EUR"


def _paid(amount: str | None, currency: str | None) -> ExternalPaymentState:
    return ExternalPaymentState(
        provider_payment_id="c-1",
        status=ExternalPaymentStatus.SUCCEEDED,
        provider_transaction_id="tx-1",
        amount=Decimal(amount) if amount else None,
        currency=currency,
    )


def test_a_different_charged_amount_or_currency_is_refused():
    attempt = PaymentAttempt(pk=1, amount=Decimal("25.00"), currency="EUR")

    _require_matching_amount(attempt=attempt, external=_paid("25.0", "EUR"))
    _require_matching_amount(attempt=attempt, external=_paid(None, None))

    with pytest.raises(PaymentReconciliationConflict):
        _require_matching_amount(
            attempt=attempt,
            external=_paid("2.50", "EUR"),
        )

    with pytest.raises(PaymentReconciliationConflict):
        _require_matching_amount(
            attempt=attempt,
            external=_paid("25.00", "SEK"),
        )


@override_settings(
    DEBUG=False,
    PAYMENT_PROVIDER="sumup",
    SUMUP_API_KEY="",
    SUMUP_MERCHANT_CODE="M123456",
)
def test_missing_sumup_key_is_reported_in_production():
    (warning,) = sumup_keys_are_set(None)

    assert warning.id == "payments.W001"
    assert "SUMUP_API_KEY" in warning.msg


@override_settings(
    DEBUG=False,
    PAYMENT_PROVIDER="sumup",
    SUMUP_API_KEY="key",
    SUMUP_MERCHANT_CODE="M123456",
)
def test_no_warning_when_the_keys_are_set():
    assert sumup_keys_are_set(None) == []
