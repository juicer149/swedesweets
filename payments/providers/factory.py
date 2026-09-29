from __future__ import annotations

from django.conf import settings

from payments.contracts import (
    HostedPaymentConfigurationError,
    HostedPaymentProvider,
)
from payments.providers.fake import FakeHostedPaymentProvider
from payments.providers.sumup import SumUpHostedPaymentProvider


def get_default_hosted_payment_provider() -> HostedPaymentProvider:
    """Build the configured hosted payment provider.

    Provider credentials stay in Django settings/environment and never leak
    into views or domain services.

    Missing credentials are reported as a hosted payment error so callers
    can treat misconfiguration like any other unavailable provider.
    """

    if settings.PAYMENT_PROVIDER == settings.PAYMENT_PROVIDER_FAKE:
        return FakeHostedPaymentProvider()

    try:
        return SumUpHostedPaymentProvider(
            api_key=settings.SUMUP_API_KEY,
            merchant_code=settings.SUMUP_MERCHANT_CODE,
        )
    except ValueError as exc:
        raise HostedPaymentConfigurationError(
            str(exc)
        ) from exc
