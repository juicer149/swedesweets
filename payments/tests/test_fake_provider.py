from __future__ import annotations

from decimal import Decimal

import pytest

from payments.contracts import (
    ExternalPaymentStatus,
    HostedPaymentRequest,
)
from payments.providers.factory import get_default_hosted_payment_provider
from payments.providers.fake import (
    FakeHostedPaymentProvider,
    FakePaymentError,
    complete_fake_payment,
)


def _request() -> HostedPaymentRequest:
    return HostedPaymentRequest(
        reference="payment-1",
        amount=Decimal("25.00"),
        currency="EUR",
        description="SwedeSweets order 1",
        customer_return_url="http://testserver/shop/payment/x/return/",
        webhook_url="http://testserver/payments/sumup/webhook/",
    )


def test_factory_returns_fake_provider_when_configured(settings):
    settings.PAYMENT_PROVIDER = "fake"

    assert isinstance(
        get_default_hosted_payment_provider(),
        FakeHostedPaymentProvider,
    )


def test_new_fake_payment_is_pending_with_hosted_url():
    provider = FakeHostedPaymentProvider()

    session = provider.create_payment(
        request=_request(),
    )
    state = provider.get_payment(
        provider_payment_id=session.provider_payment_id,
    )

    assert session.redirect_url.startswith("/payments/fake/")
    assert state.status == ExternalPaymentStatus.PENDING
    assert state.hosted_payment_url == session.redirect_url


@pytest.mark.parametrize(
    ("succeeded", "expected_status"),
    [
        (True, ExternalPaymentStatus.SUCCEEDED),
        (False, ExternalPaymentStatus.FAILED),
    ],
)
def test_completed_fake_payment_reports_final_state(
    succeeded: bool,
    expected_status: ExternalPaymentStatus,
):
    provider = FakeHostedPaymentProvider()
    session = provider.create_payment(
        request=_request(),
    )

    complete_fake_payment(
        session.provider_payment_id,
        succeeded=succeeded,
    )

    state = provider.get_payment(
        provider_payment_id=session.provider_payment_id,
    )

    assert state.status == expected_status
    assert state.hosted_payment_url is None
    assert (state.provider_transaction_id is not None) == succeeded


def test_finished_fake_payment_cannot_change_outcome():
    provider = FakeHostedPaymentProvider()
    session = provider.create_payment(
        request=_request(),
    )

    complete_fake_payment(
        session.provider_payment_id,
        succeeded=True,
    )
    complete_fake_payment(
        session.provider_payment_id,
        succeeded=False,
    )

    assert provider.get_payment(
        provider_payment_id=session.provider_payment_id,
    ).status == ExternalPaymentStatus.SUCCEEDED


def test_unknown_fake_payment_is_a_provider_error():
    with pytest.raises(FakePaymentError):
        FakeHostedPaymentProvider().get_payment(
            provider_payment_id="fake-missing",
        )


def test_fake_payment_can_be_found_by_reference():
    provider = FakeHostedPaymentProvider()
    session = provider.create_payment(
        request=_request(),
    )

    state = provider.find_payment_by_reference(
        reference="payment-1",
    )

    assert state.provider_payment_id == session.provider_payment_id


def test_unknown_fake_reference_is_not_found():
    assert FakeHostedPaymentProvider().find_payment_by_reference(
        reference="payment-missing",
    ) is None


def test_cancelled_fake_payment_reports_failed():
    provider = FakeHostedPaymentProvider()
    session = provider.create_payment(
        request=_request(),
    )

    provider.cancel_payment(
        provider_payment_id=session.provider_payment_id,
    )

    assert provider.get_payment(
        provider_payment_id=session.provider_payment_id,
    ).status == ExternalPaymentStatus.FAILED


def test_paid_fake_payment_cannot_be_cancelled():
    provider = FakeHostedPaymentProvider()
    session = provider.create_payment(
        request=_request(),
    )
    complete_fake_payment(
        session.provider_payment_id,
        succeeded=True,
    )

    with pytest.raises(FakePaymentError):
        provider.cancel_payment(
            provider_payment_id=session.provider_payment_id,
        )
