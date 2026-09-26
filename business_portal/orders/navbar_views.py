from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

from business.cart_selectors import (
    get_customer_cart,
)
from business_portal.orders.navbar_viewmodels import (
    build_business_navbar_cart,
)
from business_portal.selectors import (
    get_portal_customer_for_user,
)


@login_required
@require_GET
def navbar_cart_fragment(
    request,
):
    customer = get_portal_customer_for_user(
        user=request.user,
    )

    cart = get_customer_cart(
        customer=customer,
    )

    navbar_cart = (
        build_business_navbar_cart(
            cart=cart,
            language_code=request.LANGUAGE_CODE,
        )
    )

    return render(
        request,
        "includes/navbar_cart.html",
        {
            "navbar_cart": navbar_cart,
        },
    )
