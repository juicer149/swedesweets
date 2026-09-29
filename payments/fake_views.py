from __future__ import annotations

from django.conf import settings
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
)
from django.shortcuts import (
    redirect,
    render,
)
from django.views.decorators.http import require_http_methods

from payments.providers.fake import (
    complete_fake_payment,
    get_fake_payment,
)

FAKE_OUTCOME_PAY = "pay"
FAKE_OUTCOME_DECLINE = "decline"


@require_http_methods(
    [
        "GET",
        "POST",
    ]
)
def fake_checkout(
    request: HttpRequest,
    payment_id: str,
) -> HttpResponse:
    """Local hosted payment page for the fake provider."""

    if settings.PAYMENT_PROVIDER != settings.PAYMENT_PROVIDER_FAKE:
        raise Http404(
            "The fake payment provider is not enabled."
        )

    payment = get_fake_payment(
        payment_id
    )

    if payment is None:
        raise Http404(
            "Fake payment not found."
        )

    if request.method == "POST":
        outcome = request.POST.get(
            "outcome"
        )

        if outcome not in {
            FAKE_OUTCOME_PAY,
            FAKE_OUTCOME_DECLINE,
        }:
            return HttpResponseBadRequest(
                "Unknown outcome."
            )

        complete_fake_payment(
            payment_id,
            succeeded=outcome == FAKE_OUTCOME_PAY,
        )

        return redirect(
            payment["customer_return_url"]
        )

    return render(
        request,
        "payments/fake_checkout.html",
        {
            "payment": payment,
            "payment_id": payment_id,
            "pay_outcome": FAKE_OUTCOME_PAY,
            "decline_outcome": FAKE_OUTCOME_DECLINE,
        },
    )
