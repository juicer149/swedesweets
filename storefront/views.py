from __future__ import annotations

from uuid import UUID

from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
)
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET

from accounts.roles import AccountRole
from orders.models import Order
from payments.selectors import get_latest_payment_attempt
from retail.models import RetailCheckoutSession
from retail.payments import (
    RetailPaymentRecoveryAction,
    recover_retail_payment,
)
from storefront.checkout_session import (
    forget_checkout_details,
    owns_checkout,
)
from storefront.faq import PUBLIC_FAQ, answered

PAYMENT_RESULT_CONFIRMED = "confirmed"
PAYMENT_RESULT_FAILED = "failed"
PAYMENT_RESULT_SUPPORT = "support"


def _is_business_customer(
    request: HttpRequest,
) -> bool:
    return (
        getattr(
            request,
            "account_role",
            None,
        )
        == AccountRole.BUSINESS_CUSTOMER
    )


@require_GET
def landing(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "storefront/landing.html",
    )


@require_GET
def contact(request: HttpRequest) -> HttpResponse:
    if _is_business_customer(request):
        return redirect(
            "business_portal:contact"
        )

    return render(
        request,
        "storefront/contact.html",
    )


@require_GET
def faq(request: HttpRequest) -> HttpResponse:
    if _is_business_customer(request):
        return redirect(
            "business_portal:faq"
        )

    return render(
        request,
        "storefront/faq.html",
        {
            "faq_items": answered(PUBLIC_FAQ),
            "contact_url": reverse(
                "public_site:contact"
            ),
        },
    )


def payment_return(
    request: HttpRequest,
    checkout_id: UUID,
) -> HttpResponse:
    """Recover a retail payment after the customer returns from SumUp.

    Provider redirects are not trusted as proof of payment.

    Recovery asks the provider for authoritative state when necessary and then
    maps the resulting application state to the next customer-facing action.

    The page is reachable by checkout id alone because the buyer may return
    from the provider in a different session. It therefore shows only the
    order reference and payment outcome, never buyer details.
    """

    checkout = get_object_or_404(
        RetailCheckoutSession.objects.select_related(
            "order",
        ),
        pk=checkout_id,
    )

    attempt = get_latest_payment_attempt(
        order=checkout.order,
    )

    if attempt is None:
        raise Http404(
            "No payment attempt exists for this checkout."
        )

    recovery = recover_retail_payment(
        attempt=attempt,
    )

    match recovery.action:
        case RetailPaymentRecoveryAction.CONTINUE_PAYMENT if recovery.redirect_url:
            return HttpResponseRedirect(
                recovery.redirect_url
            )
        case RetailPaymentRecoveryAction.CONFIRMED:
            result = PAYMENT_RESULT_CONFIRMED

            forget_checkout_details(
                request
            )
        case RetailPaymentRecoveryAction.PAYMENT_FAILED:
            result = PAYMENT_RESULT_FAILED
        case _:
            result = PAYMENT_RESULT_SUPPORT

    checkout.order.refresh_from_db()

    return render(
        request,
        "storefront/checkout/payment_result.html",
        {
            "result": result,
            "order_reference": checkout.order.pk,
            "retry_url": _payment_retry_url(
                request,
                checkout=checkout,
                result=result,
            ),
            "shop_url": reverse(
                "storefront:product_list"
            ),
            "cart_url": reverse(
                "storefront:cart"
            ),
            "contact_url": reverse(
                "public_site:contact"
            ),
        },
    )


def _payment_retry_url(
    request: HttpRequest,
    *,
    checkout: RetailCheckoutSession,
    result: str,
) -> str | None:
    if result != PAYMENT_RESULT_FAILED:
        return None

    if not owns_checkout(
        request,
        checkout_id=checkout.pk,
    ):
        return None

    if checkout.order.status != Order.Status.DRAFT:
        return None

    if checkout.expires_at <= timezone.now():
        return None

    return reverse(
        "storefront:checkout_pay",
        kwargs={
            "checkout_id": checkout.pk,
        },
    )
