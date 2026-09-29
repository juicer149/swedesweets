from __future__ import annotations

import logging
from uuid import UUID

from django.contrib import messages
from django.http import (
    Http404,
    HttpRequest,
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
)

from orders.models import Order
from retail.cart_selectors import get_retail_cart
from retail.errors import (
    InvalidRetailCart,
    InvalidRetailOrder,
    RetailCheckoutPaymentInProgress,
)
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
    ).as_dict()

    return render(
        request,
        "storefront/checkout/review.html",
        context,
    )
