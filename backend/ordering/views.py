from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from catalog.read.selectors import list_orderable_products

from .authz import require_active_store, require_request_store
from .domain.errors import OrderingError
from .models import Order
from .read.selectors import get_order_for_store, list_store_orders
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


@login_required
def order_create(request):
    """
    Display and process the order form for the authenticated store.

    DESIGN:
    - resolve store from request
    - load orderable catalog projection
    - parse submitted quantities into a command
    - execute the write action
    - render validation errors without leaking write-layer exceptions directly
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

    Orders are split into:
    - open orders: pending / packed
    - delivered orders: completed history
    """
    store = require_request_store(request)
    orders = list_store_orders(store)

    open_orders = []
    delivered_orders = []

    for order in orders:
        if order.status == Order.Status.DELIVERED:
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

    The detail page can be reached from more than one parent page, so the
    back link is resolved from a small query-string source hint.
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
