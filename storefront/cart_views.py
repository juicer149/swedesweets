from __future__ import annotations

from django.contrib import messages
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    JsonResponse,
)
from django.shortcuts import (
    redirect,
    render,
)
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import (
    require_GET,
    require_http_methods,
    require_POST,
)

from carts.models import Cart, CartLine
from retail.cart_selectors import (
    get_retail_cart,
    get_retail_cart_line,
)
from retail.errors import (
    InvalidRetailCart,
    RetailCartLocked,
)
from retail.selectors import (
    get_retail_checkout_with_open_payment,
)
from retail.services import (
    clear_retail_cart,
    update_retail_cart_line_quantity,
)
from retail.services import (
    remove_retail_cart_line as remove_retail_cart_line_service,
)
from storefront.cart import (
    mark_retail_cart_active,
)
from storefront.cart_viewmodels import (
    build_retail_cart_context,
)
from storefront.checkout_session import (
    remember_checkout,
)
from storefront.navbar_viewmodels import (
    build_retail_navbar_cart,
)


CLEAR_CART_INTENT = "clear_cart"


class InvalidCartInput(ValueError):
    """Raised when cart input cannot be parsed from the HTTP request."""


def _wants_json(
    request: HttpRequest,
) -> bool:
    return (
        "application/json"
        in request.headers.get(
            "Accept",
            "",
        )
    )


def _get_request_cart(
    request: HttpRequest,
) -> Cart | None:
    return get_retail_cart(
        cart_id=getattr(
            request,
            "retail_cart_id",
            None,
        ),
    )


def _get_request_cart_or_404(
    request: HttpRequest,
) -> Cart:
    cart = _get_request_cart(
        request
    )

    if cart is None:
        raise Http404(
            "Retail cart does not exist."
        )

    return cart


def _get_request_cart_line_or_404(
    *,
    cart: Cart,
    cart_line_id: int,
) -> CartLine:
    line = get_retail_cart_line(
        cart=cart,
        line_id=cart_line_id,
    )

    if line is None:
        raise Http404(
            "Retail cart line does not exist."
        )

    return line


def _parse_quantity(
    raw_value: str | None,
) -> int:
    if raw_value is None:
        raise InvalidCartInput(
            "quantity is required"
        )

    value = raw_value.strip()

    if not value:
        raise InvalidCartInput(
            "quantity is required"
        )

    try:
        return int(value)
    except ValueError as exc:
        raise InvalidCartInput(
            "invalid quantity"
        ) from exc


def _cart_error_response(
    request: HttpRequest,
    error: Exception,
) -> HttpResponse:
    message = str(error)

    if _wants_json(request):
        return JsonResponse(
            {
                "ok": False,
                "message": message,
            },
            status=(
                409
                if isinstance(error, RetailCartLocked)
                else 400
            ),
        )

    messages.error(
        request,
        message,
    )

    return redirect(
        "storefront:cart"
    )


def _open_payment_url(
    request: HttpRequest,
    *,
    cart: Cart | None,
) -> str | None:
    """Return the review page of a checkout being paid from this cart.

    The signed cart cookie proves this browser owns the cart, and with it
    the checkout created from the cart, so ownership is remembered here
    for buyers whose session no longer lists the checkout.
    """

    if cart is None:
        return None

    checkout = get_retail_checkout_with_open_payment(
        cart=cart,
    )

    if checkout is None:
        return None

    remember_checkout(
        request,
        checkout_id=checkout.pk,
    )

    return reverse(
        "storefront:checkout_review",
        kwargs={
            "checkout_id": checkout.pk,
        },
    )


@require_http_methods(
    [
        "GET",
        "POST",
    ]
)
def cart(
    request: HttpRequest,
):
    cart = _get_request_cart(
        request
    )

    if request.method == "POST":
        intent = request.POST.get(
            "intent"
        )

        if intent == CLEAR_CART_INTENT and cart is not None:
            try:
                clear_retail_cart(
                    cart=cart,
                )
            except InvalidRetailCart as error:
                messages.error(
                    request,
                    str(error),
                )
            else:
                messages.success(
                    request,
                    _("Cart cleared."),
                )
        elif intent != CLEAR_CART_INTENT:
            messages.error(
                request,
                _("Unknown cart action."),
            )

        return redirect(
            "storefront:cart"
        )

    context = build_retail_cart_context(
        cart=cart,
        checkout_url=reverse("storefront:checkout"),
        open_payment_url=_open_payment_url(
            request,
            cart=cart,
        ),
    ).as_dict()

    return render(
        request,
        "storefront/cart.html",
        context,
    )


@require_GET
def navbar_cart_fragment(
    request: HttpRequest,
):
    cart = _get_request_cart(
        request
    )

    navbar_cart = (
        build_retail_navbar_cart(
            cart=cart,
        )
    )

    return render(
        request,
        "includes/navbar_cart.html",
        {
            "navbar_cart": navbar_cart,
        },
    )


@require_POST
def set_cart_line_quantity(
    request: HttpRequest,
    cart_line_id: int,
):
    cart = _get_request_cart_or_404(
        request
    )

    line = _get_request_cart_line_or_404(
        cart=cart,
        cart_line_id=cart_line_id,
    )

    try:
        quantity = _parse_quantity(
            request.POST.get(
                "quantity"
            )
        )

        updated_line = (
            update_retail_cart_line_quantity(
                cart=cart,
                line=line,
                quantity=quantity,
            )
        )
    except (
        InvalidRetailCart,
        InvalidCartInput,
    ) as error:
        return _cart_error_response(
            request,
            error,
        )

    mark_retail_cart_active(
        request,
        cart_id=cart.id,
    )

    message = _(
        "Quantity updated."
    )

    if _wants_json(request):
        cart_context = build_retail_cart_context(
            cart=cart,
        )
        line_view = cart_context.line(
            updated_line.id
        )

        return JsonResponse(
            {
                "ok": True,
                "message": str(message),
                "quantity": updated_line.quantity,
                "line_total_label": (
                    line_view.line_total_label
                    if line_view is not None
                    else None
                ),
                "subtotal_label": (
                    cart_context.subtotal_label
                ),
            }
        )

    messages.success(
        request,
        message,
    )

    return redirect(
        "storefront:cart"
    )


@require_POST
def remove_cart_line(
    request: HttpRequest,
    cart_line_id: int,
):
    cart = _get_request_cart_or_404(
        request
    )

    line = _get_request_cart_line_or_404(
        cart=cart,
        cart_line_id=cart_line_id,
    )

    try:
        remove_retail_cart_line_service(
            cart=cart,
            line=line,
        )
    except InvalidRetailCart as error:
        return _cart_error_response(
            request,
            error,
        )

    mark_retail_cart_active(
        request,
        cart_id=cart.id,
    )

    message = _(
        "Product removed from your cart."
    )

    if _wants_json(request):
        return JsonResponse(
            {
                "ok": True,
                "message": str(message),
            }
        )

    messages.success(
        request,
        message,
    )

    return redirect(
        "storefront:cart"
    )
