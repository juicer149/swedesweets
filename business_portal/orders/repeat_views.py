from __future__ import annotations

from typing import assert_never

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.translation import (
    gettext as _,
)
from django.utils.translation import (
    ngettext,
)
from django.views.decorators.http import require_POST

from business.repeat_services import (
    RepeatOrderResult,
    RepeatOrderSkipReason,
    repeat_order_into_cart,
)
from business_portal.orders.cart_viewmodels import (
    build_portal_cart_lines,
)
from business_portal.orders.selectors import (
    get_portal_order_for_user,
)
from business_portal.selectors import (
    get_portal_customer_for_user,
)
from common.http import wants_json
from products.localization import translated_product_name


@login_required
@require_POST
def repeat_order(
    request,
    order_id: int,
):
    customer = get_portal_customer_for_user(
        user=request.user,
    )

    source_order = get_portal_order_for_user(
        user=request.user,
        order_id=order_id,
    )

    result = repeat_order_into_cart(
        customer=customer,
        source_order=source_order,
    )

    if wants_json(request):
        return _repeat_json_response(
            request,
            result=result,
        )

    if result.added_count:
        messages.success(
            request,
            ngettext(
                "%(count)s order item was added to your cart.",
                "%(count)s order items were added to your cart.",
                result.added_count,
            )
            % {
                "count": result.added_count,
            },
        )

    for skipped in result.skipped:
        product_name = translated_product_name(
            skipped.product,
            language_code=request.LANGUAGE_CODE,
        )

        messages.warning(
            request,
            _skip_message(
                product_name=product_name,
                reason=skipped.reason,
            ),
        )

    if result.has_added_lines:
        return redirect(
            "business_portal:cart"
        )

    return redirect(
        "business_portal:order_detail",
        order_id=source_order.id,
    )


def _repeat_json_response(
    request,
    *,
    result: RepeatOrderResult,
) -> JsonResponse:
    """The cart page's "Order again" (business_cart.js): the lines it
    added or raised, drawn, for the page to put in place; and why any
    product was left out, to say beside the order."""

    notes = [
        _skip_message(
            product_name=translated_product_name(
                skipped.product,
                language_code=request.LANGUAGE_CODE,
            ),
            reason=skipped.reason,
        )
        for skipped in result.skipped
    ]

    lines = (
        build_portal_cart_lines(
            cart=result.cart,
            cart_line_ids=result.added_line_ids,
            language_code=request.LANGUAGE_CODE,
        )
        if result.cart is not None
        else ()
    )

    return JsonResponse(
        {
            "ok": result.has_added_lines,
            "notes": notes,
            "lines": [
                {
                    "cart_line_id": line.cart_line_id,
                    "quantity": line.quantity,
                    "line_html": render_to_string(
                        "business_portal/orders/includes/cart_line.html",
                        {"line": line},
                        request=request,
                    ),
                }
                for line in lines
            ],
        },
        status=200 if result.has_added_lines else 400,
    )


def _skip_message(
    *,
    product_name: str,
    reason: RepeatOrderSkipReason,
) -> str:
    match reason:
        case RepeatOrderSkipReason.PRODUCT_UNAVAILABLE:
            return _(
                "%(product)s is no longer available for business ordering."
            ) % {
                "product": product_name,
            }

        case RepeatOrderSkipReason.OFFER_UNAVAILABLE:
            return _(
                "%(product)s was not added because the original offer "
                "is no longer available."
            ) % {
                "product": product_name,
            }

    assert_never(reason)
