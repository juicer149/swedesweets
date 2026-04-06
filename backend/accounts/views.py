from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .authz import (
    is_staff_user,
    is_store_user,
    require_staff_user,
    require_store_user,
)
from .read.selectors import (
    count_staff_open_orders,
    count_staff_unprocessed_partner_requests,
    get_store_portal_snapshot,
    list_staff_open_orders,
    list_staff_unprocessed_partner_requests,
    public_store_locator_entries,
)


def store_list(request):
    """
    Public store locator page.

    Shows active stores with a usable address so visitors can find retail
    locations that carry SwedeSweets products.
    """
    return render(
        request,
        "accounts/store_list.html",
        {"stores": public_store_locator_entries()},
    )


@login_required
def portal(request):
    """
    Smart authenticated entrypoint.

    Routing rules:
    - store users go to the store portal
    - internal staff users go to the staff portal
    - other authenticated users get a fallback page
    """
    if is_store_user(request.user):
        return redirect("accounts:store_portal")

    if is_staff_user(request.user):
        return redirect("accounts:staff_portal")

    return render(
        request,
        "accounts/no_store_connected.html",
        status=403,
    )


@login_required
def store_portal(request):
    """
    Portal for store-linked partner accounts.

    Responsibility:
    - resolve the Store linked to the authenticated user
    - show store-facing overview data
    - act as entrypoint into ordering

    Non-responsibility:
    - staff operations
    - system administration
    """
    store = require_store_user(request)
    context = get_store_portal_snapshot(store)

    return render(
        request,
        "accounts/store_portal.html",
        context,
    )


@login_required
def staff_portal(request):
    """
    Internal staff portal.

    This is the lightweight operational surface for internal users who need to
    monitor open orders and incoming partner requests without using full Django
    admin for every task.
    """
    require_staff_user(request)

    context = {
        "open_orders": list_staff_open_orders(limit=10),
        "unprocessed_partner_requests": list_staff_unprocessed_partner_requests(limit=10),
        "open_order_count": count_staff_open_orders(),
        "unprocessed_partner_request_count": count_staff_unprocessed_partner_requests(),
    }

    return render(
        request,
        "accounts/staff_portal.html",
        context,
    )
