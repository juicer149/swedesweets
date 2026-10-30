from __future__ import annotations

from enum import StrEnum

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
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
from common.cart_price_feedback import cart_price_feedback
from common.channels import SalesChannel
from common.http import wants_json
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

    as_json = wants_json(
        request
    )

    previous_subtotal = (
        build_portal_cart_context(cart=line.cart).subtotal if as_json else None
    )
    previous_quantity = line.quantity

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

        if as_json:
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

        if as_json:
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

        if as_json:
            current = build_portal_cart_line(
                cart=line.cart,
                cart_line_id=line.id,
                language_code=request.LANGUAGE_CODE,
            )
            return JsonResponse(
                {
                    "ok": True,
                    "message": str(message),
                    "quantity": quantity,
                    "change_direction": (
                        (quantity > previous_quantity) - (quantity < previous_quantity)
                    ),
                    "line_total_label": current.line_total_label if current else None,
                    **cart_price_feedback(
                        previous_subtotal,
                        build_portal_cart_context(cart=line.cart).subtotal,
                    ),
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

    as_json = wants_json(
        request
    )

    before = build_portal_cart_context(cart=line.cart).subtotal if as_json else None
    cart = line.cart

    try:
        remove_customer_cart_line(
            customer=customer,
            line=line,
        )
    except InvalidBusinessCart as error:
        message = str(error)

        if as_json:
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

        if as_json:
            return JsonResponse(
                {
                    "ok": True,
                    "message": str(message),
                    "cart_line_id": line.id,
                    "change_direction": -1,
                    **cart_price_feedback(
                        before,
                        build_portal_cart_context(cart=cart).subtotal,
                    ),
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
                    extra_tags="cart-notice",
                )

                return redirect(
                    "business_portal:catalog"
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
    """Add one unit of each selected offer in one transaction.

    JSON returns confirmed rows and one subtotal delta. Single-offer callers
    retain their line fields, and native forms still redirect to the cart.
    """

    customer = get_portal_customer_for_user(
        user=request.user,
    )
    as_json = wants_json(request)
    before = (
        build_portal_cart_context(cart=get_customer_cart(customer=customer)).subtotal
        if as_json else None
    )

    try:
        raw_ids = request.POST.getlist("commercial_price_id")
        try:
            offer_ids = list(dict.fromkeys(int(value) for value in raw_ids))
        except (ValueError, TypeError):
            offer_ids = []
        if not offer_ids or len(raw_ids) > 100:
            raise InvalidBusinessCart(_("Choose a product to add."))
        offers = {
            offer.pk: offer
            for offer in CommercialPrice.objects.select_related("product").filter(
                pk__in=offer_ids,
            )
        }
        if len(offers) != len(offer_ids):
            raise InvalidBusinessCart(_("Choose a product to add."))
        with transaction.atomic():
            lines = [
                add_catalog_offer_to_cart(
                    customer=customer,
                    product=offers[offer_id].product,
                    commercial_price_id=offer_id,
                    quantity=1,
                )
                for offer_id in offer_ids
            ]

    except InvalidBusinessCart as error:
        message = str(error)

        if as_json:
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
        "product": ", ".join(
            translated_product_name(
                offers[offer_id].product, language_code=request.LANGUAGE_CODE,
            )
            for offer_id in offer_ids
        ),
    }
    if not as_json:
        messages.success(request, message, extra_tags="cart-notice cart-flow-notice")
        return redirect("business_portal:cart")

    rendered_lines = [
        {
            "cart_line_id": line.id,
            "quantity": line.quantity,
            "line_html": render_to_string(
                "business_portal/orders/includes/cart_line.html",
                {"line": build_portal_cart_line(
                    cart=line.cart, cart_line_id=line.id,
                    language_code=request.LANGUAGE_CODE,
                )},
                request=request,
            ),
        }
        for line in lines
    ]
    return JsonResponse({
        "ok": True,
        "message": message,
        "lines": rendered_lines,
        **(rendered_lines[0] if len(rendered_lines) == 1 else {}),
        "change_direction": 1,
        **cart_price_feedback(
            before, build_portal_cart_context(cart=lines[0].cart).subtotal,
        ),
    })


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
                    extra_tags="cart-notice",
                )

                return redirect(
                    "business_portal:catalog"
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
