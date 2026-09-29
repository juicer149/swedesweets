from __future__ import annotations

import logging
from uuid import UUID

from django.contrib import messages
from django.http import (
    Http404,
    HttpRequest,
    JsonResponse,
)
from django.shortcuts import (
    redirect,
    render,
)
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import (
    require_GET,
    require_http_methods,
    require_POST,
)

from inventory.errors import InsufficientStockError
from orders.models import Order
from payments.errors import HostedPaymentError
from payments.selectors import get_pending_payment_attempt
from retail.cart_selectors import get_retail_cart
from retail.delivery_areas import RETAIL_SERVICE_COUNTRY
from retail.errors import (
    InvalidRetailCart,
    InvalidRetailOrder,
    RetailCheckoutPaymentInProgress,
)
from retail.models import RetailCheckoutSession
from retail.payments import (
    RetailPaymentRecoveryAction,
    begin_retail_hosted_payment,
    cancel_open_retail_payment,
)
from retail.rules import list_retail_cities_for_postal_code
from retail.selectors import get_retail_checkout
from retail.services import create_retail_checkout_from_cart
from storefront.cart_viewmodels import build_retail_cart_context
from storefront.checkout_forms import RetailCheckoutDetailsForm
from storefront.checkout_session import (
    get_remembered_checkout_details,
    owns_checkout,
    remember_checkout,
    remember_checkout_details,
)
from storefront.checkout_viewmodels import build_checkout_review_context

logger = logging.getLogger(__name__)


def _get_owned_checkout_or_404(
    request: HttpRequest,
    checkout_id: UUID,
) -> RetailCheckoutSession:
    if not owns_checkout(
        request,
        checkout_id=checkout_id,
    ):
        raise Http404(
            "Checkout not found."
        )

    checkout = get_retail_checkout(
        checkout_id=checkout_id,
    )

    if checkout is None:
        raise Http404(
            "Checkout not found."
        )

    return checkout


@require_GET
def checkout_cities(
    request: HttpRequest,
):
    """Return deliverable town names for one postal code.

    Public reference data used to prefill the town on the checkout form.
    """

    postal_code = request.GET.get(
        "postal_code",
        "",
    )

    return JsonResponse(
        {
            "cities": list_retail_cities_for_postal_code(
                country_code=RETAIL_SERVICE_COUNTRY,
                postal_code=postal_code,
            ),
        }
    )


@require_http_methods(
    [
        "GET",
        "POST",
    ]
)
def checkout_details(
    request: HttpRequest,
):
    cart = get_retail_cart(
        cart_id=getattr(
            request,
            "retail_cart_id",
            None,
        ),
    )

    if cart is None or not cart.lines.exists():
        messages.info(
            request,
            _("Your cart is empty."),
        )

        return redirect(
            "storefront:cart"
        )

    if request.method == "POST":
        form = RetailCheckoutDetailsForm(
            request.POST,
        )

        if form.is_valid():
            try:
                checkout = create_retail_checkout_from_cart(
                    cart=cart,
                    buyer=form.to_buyer_input(),
                )
            except RetailCheckoutPaymentInProgress as exc:
                remember_checkout(
                    request,
                    checkout_id=exc.checkout.pk,
                )

                messages.info(
                    request,
                    _(
                        "You already have a payment in progress "
                        "for this cart."
                    ),
                )

                return redirect(
                    "storefront:checkout_review",
                    checkout_id=exc.checkout.pk,
                )
            except (
                InvalidRetailCart,
                InvalidRetailOrder,
            ) as exc:
                logger.info(
                    "Retail checkout rejected for cart %s: %s",
                    cart.pk,
                    exc,
                )

                form.add_error(
                    None,
                    _(
                        "Some items in your cart are no longer available. "
                        "Review your cart and try again."
                    ),
                )
            else:
                remember_checkout(
                    request,
                    checkout_id=checkout.pk,
                )
                remember_checkout_details(
                    request,
                    details=form.session_data(),
                )

                return redirect(
                    "storefront:checkout_review",
                    checkout_id=checkout.pk,
                )
    else:
        form = RetailCheckoutDetailsForm(
            initial=get_remembered_checkout_details(
                request
            ),
        )

    return render(
        request,
        "storefront/checkout/details.html",
        {
            "form": form,
            "cart_summary": build_retail_cart_context(
                cart=cart,
            ),
            "cart_url": reverse(
                "storefront:cart"
            ),
        },
    )


@require_GET
def checkout_review(
    request: HttpRequest,
    checkout_id: UUID,
):
    checkout = _get_owned_checkout_or_404(
        request,
        checkout_id,
    )

    order = checkout.order

    if order.status == Order.Status.CANCELLED:
        messages.info(
            request,
            _(
                "This checkout was replaced by a newer one. "
                "Please confirm your details again."
            ),
        )

        return redirect(
            "storefront:checkout"
        )

    if order.status != Order.Status.DRAFT:
        return redirect(
            "storefront:payment_return",
            checkout_id=checkout.pk,
        )

    if checkout.expires_at <= timezone.now():
        messages.info(
            request,
            _(
                "Your checkout has expired. "
                "Please confirm your details again."
            ),
        )

        return redirect(
            "storefront:checkout"
        )

    context = build_checkout_review_context(
        checkout=checkout,
        has_open_payment=get_pending_payment_attempt(
            order=order,
        ) is not None,
    ).as_dict()

    return render(
        request,
        "storefront/checkout/review.html",
        context,
    )


@require_POST
def checkout_pay(
    request: HttpRequest,
    checkout_id: UUID,
):
    """Send the buyer to the hosted payment page for one checkout.

    Invariant: a new external payment is never started while an earlier
    PENDING attempt has an unknown outcome. Any pending attempt, with or
    without a provider payment id, is resolved through the payment return
    flow, where recovery decides between resuming, confirming, failing or
    routing to support.
    """

    checkout = _get_owned_checkout_or_404(
        request,
        checkout_id,
    )
    order = checkout.order

    if order.status != Order.Status.DRAFT:
        return redirect(
            "storefront:payment_return",
            checkout_id=checkout.pk,
        )

    if get_pending_payment_attempt(
        order=order,
    ) is not None:
        return redirect(
            "storefront:payment_return",
            checkout_id=checkout.pk,
        )

    try:
        payment = begin_retail_hosted_payment(
            checkout=checkout,
            customer_return_url=request.build_absolute_uri(
                reverse(
                    "storefront:payment_return",
                    kwargs={
                        "checkout_id": checkout.pk,
                    },
                )
            ),
            webhook_url=request.build_absolute_uri(
                reverse(
                    "payments:sumup_webhook"
                )
            ),
        )
    except InsufficientStockError:
        messages.error(
            request,
            _(
                "Some items in your cart are no longer in stock. "
                "Please update your cart."
            ),
        )

        return redirect(
            "storefront:cart"
        )
    except InvalidRetailOrder:
        if get_pending_payment_attempt(
            order=order,
        ) is not None:
            return redirect(
                "storefront:payment_return",
                checkout_id=checkout.pk,
            )

        messages.info(
            request,
            _(
                "Your checkout has expired. "
                "Please confirm your details again."
            ),
        )

        return redirect(
            "storefront:checkout"
        )
    except HostedPaymentError:
        logger.warning(
            "Hosted payment setup failed for checkout %s",
            checkout.pk,
            exc_info=True,
        )

        if get_pending_payment_attempt(
            order=order,
        ) is not None:
            return redirect(
                "storefront:payment_return",
                checkout_id=checkout.pk,
            )

        messages.error(
            request,
            _(
                "We couldn't reach the payment provider. "
                "Please try again in a moment."
            ),
        )

        return redirect(
            "storefront:checkout_review",
            checkout_id=checkout.pk,
        )

    return redirect(
        payment.redirect_url
    )


@require_POST
def checkout_cancel_payment(
    request: HttpRequest,
    checkout_id: UUID,
):
    """Cancel the buyer's open payment so the order can be changed.

    A payment completed in the meantime wins: the buyer is sent to the
    confirmation page instead of back to the cart.
    """

    checkout = _get_owned_checkout_or_404(
        request,
        checkout_id,
    )

    attempt = get_pending_payment_attempt(
        order=checkout.order,
    )

    if attempt is None:
        return redirect(
            "storefront:cart"
        )

    try:
        recovery = cancel_open_retail_payment(
            attempt=attempt,
        )
    except HostedPaymentError:
        logger.warning(
            "Could not cancel payment for checkout %s",
            checkout.pk,
            exc_info=True,
        )

        messages.error(
            request,
            _(
                "We couldn't reach the payment provider to cancel your "
                "payment. Please try again in a moment."
            ),
        )

        return redirect(
            "storefront:checkout_review",
            checkout_id=checkout.pk,
        )

    match recovery.action:
        case RetailPaymentRecoveryAction.CONFIRMED:
            return redirect(
                "storefront:payment_return",
                checkout_id=checkout.pk,
            )
        case (
            RetailPaymentRecoveryAction.PAYMENT_CANCELLED
            | RetailPaymentRecoveryAction.PAYMENT_FAILED
        ):
            messages.info(
                request,
                _(
                    "Your payment was cancelled. "
                    "You can now change your order."
                ),
            )

            return redirect(
                "storefront:cart"
            )
        case _:
            messages.error(
                request,
                _(
                    "We couldn't cancel your payment. If you already paid, "
                    "your order is safe. Otherwise, please try again or "
                    "contact us."
                ),
            )

            return redirect(
                "storefront:checkout_review",
                checkout_id=checkout.pk,
            )
