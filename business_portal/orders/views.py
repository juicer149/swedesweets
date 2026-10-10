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
from django.template.loader import render_to_string
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
    add_catalog_offer_to_cart,
    clear_customer_cart,
    remove_customer_cart_line,
    set_customer_cart_line_quantity,
)
from business.services import (
    place_customer_cart,
)
from business_portal.orders.cart_viewmodels import (
    build_portal_cart_context,
    build_portal_cart_line,
)
from business_portal.orders.detail_viewmodels import (
    build_portal_order_detail_context,
)
from business_portal.orders.quick_add import (
    build_cart_quick_add_options,
)
from business_portal.orders.recent_orders import build_recent_orders
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
from pricing.models import CommercialPrice
from products.localization import translated_product_name


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
    quick_add_options = build_cart_quick_add_options(
        language_code=request.LANGUAGE_CODE,
    )
    context["quick_add_options"] = quick_add_options
    context["recent_orders"] = build_recent_orders(
        customer=customer,
        language_code=request.LANGUAGE_CODE,
        orderable_offer_ids={
            option.commercial_price_id
            for option in quick_add_options
        },
    )

    return render(
        request,
        "business_portal/orders/cart.html",
        context,
    )


@login_required
@require_POST
def add_cart_offer(request):
    """The cart's quick add: one of the catalog's offers, one unit (again
    adds one more). Asked for JSON (cart_quick_add.js) it answers with the
    line drawn, for the page to put in place; otherwise back to the cart.
    """

    customer = get_portal_customer_for_user(
        user=request.user,
    )
    wants_json = _wants_json(request)

    try:
        commercial_price_id = int(
            request.POST.get("commercial_price_id", "")
        )
    except ValueError:
        commercial_price_id = None

    offer = (
        CommercialPrice.objects
        .select_related("product")
        .filter(pk=commercial_price_id)
        .first()
        if commercial_price_id
        else None
    )

    try:
        if offer is None:
            raise InvalidBusinessCart(
                _("Choose a product to add.")
            )

        line = add_catalog_offer_to_cart(
            customer=customer,
            product=offer.product,
            commercial_price_id=offer.pk,
            quantity=1,
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
        return redirect("business_portal:cart")

    message = _("%(product)s added to your cart.") % {
        "product": translated_product_name(
            offer.product,
            language_code=request.LANGUAGE_CODE,
        ),
    }

    if not wants_json:
        messages.success(
            request,
            message,
        )
        return redirect("business_portal:cart")

    cart_line = build_portal_cart_line(
        cart=line.cart,
        cart_line_id=line.id,
        language_code=request.LANGUAGE_CODE,
    )

    return JsonResponse(
        {
            "ok": True,
            "message": message,
            "cart_line_id": line.id,
            "quantity": line.quantity,
            "line_html": render_to_string(
                "business_portal/orders/includes/cart_line.html",
                {"line": cart_line},
                request=request,
            ),
        }
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

                # ?placed: the order page greets it with the crown.
                return redirect(
                    reverse(
                        "business_portal:order_detail",
                        kwargs={"order_id": placed_order.id},
                    )
                    + "?placed=1"
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
    # Just placed (the review page's Place order lands here with ?placed).
    context["just_placed"] = request.GET.get("placed") == "1"

    return render(
        request,
        "business_portal/orders/detail.html",
        context,
    )
