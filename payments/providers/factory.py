from __future__ import annotations

from django.conf import settings

from payments.contracts import HostedPaymentConfigurationError
from payments.providers.sumup import SumUpHostedPaymentProvider


def get_default_hosted_payment_provider() -> SumUpHostedPaymentProvider:
    """Build the configured hosted payment provider.

    Provider credentials stay in Django settings/environment and never leak
    into views or domain services.

    Missing credentials are reported as a hosted payment error so callers
    can treat misconfiguration like any other unavailable provider.
    """

    try:
        return SumUpHostedPaymentProvider(
            api_key=settings.SUMUP_API_KEY,
            merchant_code=settings.SUMUP_MERCHANT_CODE,
        )
    except ValueError as exc:
        raise HostedPaymentConfigurationError(
            str(exc)
        ) from exc
