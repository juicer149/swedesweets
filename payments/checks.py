"""System checks: missing SumUp keys show up when the site starts (in the
deploy log), not only when the first buyer tries to pay."""

from __future__ import annotations

from django.conf import settings
from django.core.checks import Warning, register


@register()
def sumup_keys_are_set(app_configs, **kwargs):
    if settings.DEBUG:
        return []

    if settings.PAYMENT_PROVIDER != settings.PAYMENT_PROVIDER_SUMUP:
        return []

    missing = [
        name
        for name in ("SUMUP_API_KEY", "SUMUP_MERCHANT_CODE")
        if not getattr(settings, name)
    ]

    if not missing:
        return []

    # A warning, not an error: the site still starts (the shop's other
    # pages work), but every payment fails until the keys are set.
    return [
        Warning(
            f"{', '.join(missing)} not set: shop payments will fail.",
            hint="Set them in the Railway variables.",
            id="payments.W001",
        )
    ]
