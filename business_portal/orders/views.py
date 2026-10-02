from __future__ import annotations

from enum import StrEnum

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import (
    require_GET,
    require_POST,
)

from business.cart_selectors import (
    get_customer_cart,
)
from business.cart_services import (
    InvalidBusinessCart,
    clear_customer_cart,
    remove_customer_cart_line,
    set_customer_cart_line_quantity,
)
from business.services import (
    place_customer_cart,
)
from business_portal.orders.cart_viewmodels import (
    build_portal_cart_context,
)
from business_portal.orders.detail_viewmodels import (
    build_portal_order_detail_context,
)
from business_portal.orders.review_viewmodels import (
    build_portal_order_review_context,
)
from business_portal.orders.selectors import (
    get_portal_order_for_user,
)
from business_portal.selectors import (
    get_portal_customer_for_user,
)
from carts.models import CartLine
from common.channels import SalesChannel
from customers.models import Customer
from inventory.errors import InvalidStockOperation
from orders.errors import InvalidOrderOperation


class PortalOrderIntent(StrEnum):
    REVIEW_ORDER = "review_order"
    PLACE_ORDER = "place_order"
    CLEAR_CART = "clear_cart"


ORDER_OPERATION_ERRORS = (
    InvalidOrderOperation,
    InvalidStockOperation,
)


def _wants_json(
    request,
) -> bool:
    return (
        "application/json"
        in request.headers.get(
            "Accept",
            "",
        )
    )


def _get_portal_cart_line(
    *,
    customer: Customer,
    cart_line_id: int,
) -> CartLine:
    return get_object_or_404(
        CartLine.objects.select_related(
            "cart",
            "commercial_price",
            "commercial_price__product",
        ),
        pk=cart_line_id,
        cart__channel=SalesChannel.BUSINESS,
        cart__business_context__customer=customer,
    )


@login_required
@require_POST
def set_cart_line_quantity(
    request,
    cart_line_id: int,
):
    customer = get_portal_customer_for_user(
        user=request.user,
    )

    line = _get_portal_cart_line(
        customer=customer,
        cart_line_id=cart_line_id,
    )

    wants_json = _wants_json(
        request
    )

    raw_quantity = request.POST.get(
        "quantity",
        "",
    ).strip()

    try:
        quantity = int(
            raw_quantity
        )
    except ValueError:
        message = _(
            "Quantity must be a whole number."
        )

        if wants_json:
            return JsonResponse(
                {
                    "ok": False,
                    "message": str(message),
                },
                status=400,
            )

        messages.error(
            request,
            message,
        )

        return redirect(
            "business_portal:cart"
        )

    try:
        set_customer_cart_line_quantity(
            customer=customer,
            line=line,
            quantity=quantity,
        )
    except InvalidBusinessCart as error:
        message = str(error)

        if wants_json:
            return JsonResponse(
                {
                    "ok": False,
                    "message": message,
                },
                status=400,
            )

        messages.error(
            request,
            message,
        )
    else:
        message = _(
            "Quantity updated."
        )

        if wants_json:
            return JsonResponse(
                {
                    "ok": True,
                    "message": str(message),
                    "quantity": quantity,
                }
            )

        messages.success(
            request,
            message,
        )

    return redirect(
        "business_portal:cart"
    )


@login_required
@require_POST
def remove_cart_line(
    request,
    cart_line_id: int,
):
    customer = get_portal_customer_for_user(
        user=request.user,
    )

    line = _get_portal_cart_line(
        customer=customer,
        cart_line_id=cart_line_id,
    )

    wants_json = _wants_json(
        request
    )

    try:
        remove_customer_cart_line(
            customer=customer,
            line=line,
        )
    except InvalidBusinessCart as error:
        message = str(error)

        if wants_json:
            return JsonResponse(
                {
                    "ok": False,
                    "message": message,
                },
                status=400,
            )

        messages.error(
            request,
            message,
        )
    else:
        message = _(
            "Product removed from your cart."
        )

        if wants_json:
            return JsonResponse(
                {
                    "ok": True,
                    "message": str(message),
                    "cart_line_id": line.id,
                }
            )

        messages.success(
            request,
            message,
        )

    return redirect(
        "business_portal:cart"
    )


@login_required
@require_GET
def orders(request):
    target = reverse(
        "business_portal:index"
    )

    query_params = request.GET.copy()
    query_params["tab"] = "orders"

    query_string = query_params.urlencode()

    if query_string:
        target = (
            f"{target}?{query_string}"
        )

    return redirect(target)


@login_required
def cart(request):
    customer = get_portal_customer_for_user(
        user=request.user,
    )

    cart = get_customer_cart(
        customer=customer,
    )

    if request.method == "POST":
        try:
            intent = PortalOrderIntent(
                request.POST.get(
                    "intent",
                    PortalOrderIntent.REVIEW_ORDER,
                )
            )
        except ValueError:
            messages.error(
                request,
                _("Unknown order action."),
            )

            return redirect(
                "business_portal:cart"
            )

        match intent:
            case PortalOrderIntent.CLEAR_CART:
                clear_customer_cart(
                    customer=customer,
                )

                messages.success(
                    request,
                    _("Cart cleared."),
                )

                return redirect(
                    "after_login"
                )

            case PortalOrderIntent.REVIEW_ORDER:
                if (
                    cart is None
                    or not cart.lines.exists()
                ):
                    messages.error(
                        request,
                        _("Add at least one product."),
                    )

                    return redirect(
                        "business_portal:cart"
                    )

                return redirect(
                    "business_portal:cart_review"
                )

            case _:
                messages.error(
                    request,
                    _("Unknown order action."),
                )

                return redirect(
                    "business_portal:cart"
                )

    context = build_portal_cart_context(
        cart=cart,
        language_code=request.LANGUAGE_CODE,
    ).as_dict()

    return render(
        request,
        "business_portal/orders/cart.html",
        context,
    )


@login_required
def cart_review(request):
    customer = get_portal_customer_for_user(
        user=request.user,
    )

    cart = get_customer_cart(
        customer=customer,
    )

    if (
        cart is None
        or not cart.lines.exists()
    ):
        messages.info(
            request,
            _("No cart to review."),
        )

        return redirect(
            "business_portal:cart"
        )

    if request.method == "POST":
        try:
            intent = PortalOrderIntent(
                request.POST.get(
                    "intent",
                    PortalOrderIntent.PLACE_ORDER,
                )
            )
        except ValueError:
            messages.error(
                request,
                _("Unknown order action."),
            )

            return redirect(
                "business_portal:cart_review"
            )

        match intent:
            case PortalOrderIntent.CLEAR_CART:
                clear_customer_cart(
                    customer=customer,
                )

                messages.success(
                    request,
                    _("Cart cleared."),
                )

                return redirect(
                    "after_login"
                )

            case PortalOrderIntent.PLACE_ORDER:
                try:
                    placed_order = place_customer_cart(
                        customer=customer,
                        user=request.user,
                    )
                except ORDER_OPERATION_ERRORS as error:
                    messages.error(
                        request,
                        str(error),
                    )

                    return redirect(
                        "business_portal:cart_review"
                    )

                messages.success(
                    request,
                    _(
                        "Order #%(order_id)s placed."
                    )
                    % {
                        "order_id": placed_order.id,
                    },
                )

                return redirect(
                    "business_portal:order_detail",
                    order_id=placed_order.id,
                )

            case _:
                messages.error(
                    request,
                    _("Unknown order action."),
                )

                return redirect(
                    "business_portal:cart_review"
                )

    context = build_portal_order_review_context(
        cart=cart,
        language_code=request.LANGUAGE_CODE,
    ).as_dict()

    return render(
        request,
        "business_portal/orders/review.html",
        context,
    )


@login_required
def order_detail(
    request,
    order_id: int,
):
    order = get_portal_order_for_user(
        user=request.user,
        order_id=order_id,
    )

    context = build_portal_order_detail_context(
        order=order,
        language_code=request.LANGUAGE_CODE,
    ).as_dict()

    return render(
        request,
        "business_portal/orders/detail.html",
        context,
    )
