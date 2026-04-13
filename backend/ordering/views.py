from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.authz import require_internal_staff_user, resolve_account_role
from accounts.domain.roles import AccountRole
from catalog.read.selectors import list_orderable_products

from .authz import require_active_store, require_request_store
from .domain.errors import OrderingError
from .models import Order
from .read.selectors import (
    get_order_for_staff,
    get_order_for_store,
    list_order_history_for_staff,
    list_store_orders,
)
from .write import dispatch_staff_order_action
from .write.actions import place_order
from .write.parsing import empty_order_form, parse_order_form


def _resolve_order_detail_back_link(source: str | None) -> tuple[str, str]:
    """
    Resolve where the order detail page should link back to.

    Supported sources:
    - portal
    - history

    Unknown values fall back to order history because that is the safest
    stable parent page for order detail.
    """
    if source == "portal":
        return "accounts:store_portal", "Back to portal"

    return "ordering:order_history", "Back to order history"


def _resolve_staff_order_work_return_url(request) -> str:
    """
    Resolve which staff portal the user should return to after completing
    an operational order action.
    """
    role = resolve_account_role(request.user)

    if role == AccountRole.FULL_STAFF:
        return "accounts:staff_portal"

    return "accounts:restricted_staff_portal"


@login_required
def order_create(request):
    """
    Display and process the order form for the authenticated store.
    """
    store = require_request_store(request)
    require_active_store(store)

    products = list_orderable_products()

    if request.method == "POST":
        form = parse_order_form(products, request.POST)

        if not form.is_valid:
            return render(
                request,
                "ordering/order_form.html",
                {
                    "store": store,
                    "form": form,
                },
                status=400,
            )

        try:
            place_order(form.to_command(store_id=store.id))
        except OrderingError as exc:
            form = form.add_error(str(exc))
            return render(
                request,
                "ordering/order_form.html",
                {
                    "store": store,
                    "form": form,
                },
                status=400,
            )

        return redirect("ordering:order_history")

    form = empty_order_form(products)
    return render(
        request,
        "ordering/order_form.html",
        {
            "store": store,
            "form": form,
        },
    )


@login_required
def order_history(request):
    """
    Show historical orders for the authenticated store.
    """
    store = require_request_store(request)
    orders = list_store_orders(store)

    open_orders = []
    delivered_orders = []

    for order in orders:
        if order.status in (Order.Status.DELIVERED, Order.Status.CANCELLED):
            delivered_orders.append(order)
        else:
            open_orders.append(order)

    return render(
        request,
        "ordering/order_history.html",
        {
            "store": store,
            "open_orders": open_orders,
            "delivered_orders": delivered_orders,
        },
    )


@login_required
def order_detail(request, order_id):
    """
    Show one order belonging to the authenticated store.
    """
    store = require_request_store(request)
    order = get_order_for_store(store, order_id)

    source = request.GET.get("from")
    back_url_name, back_label = _resolve_order_detail_back_link(source)

    return render(
        request,
        "ordering/order_detail.html",
        {
            "store": store,
            "order": order,
            "back_url_name": back_url_name,
            "back_label": back_label,
        },
    )


@login_required
def staff_order_history(request):
    """
    Show delivered and cancelled order history for internal staff.

    This is separate from the operations home so the primary portal stays
    focused on active work.
    """
    require_internal_staff_user(request)

    status_filter = request.GET.get("status", "all")
    sort = request.GET.get("sort", "date")

    orders = list_order_history_for_staff(
        status_filter=status_filter,
        sort=sort,
    )

    return render(
        request,
        "ordering/staff_order_history.html",
        {
            "orders": orders,
            "status_filter": status_filter,
            "sort": sort,
        },
    )


@login_required
def staff_order_work(request, order_id):
    """
    Internal staff work surface for one order.
    """
    require_internal_staff_user(request)
    order = get_order_for_staff(order_id)

    if request.method == "POST":
        action = request.POST.get("action", "save")
        staff_notes = request.POST.get("staff_notes", "")

        success_message = dispatch_staff_order_action(
            action=action,
            order=order,
            staff_notes=staff_notes,
        )
        messages.success(request, success_message)

        if action == "save":
            return redirect("ordering:staff_order_work", order_id=order.id)

        return redirect(_resolve_staff_order_work_return_url(request))

    return render(
        request,
        "ordering/staff_order_work.html",
        {
            "order": order,
        },
    )
