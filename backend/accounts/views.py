from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .authz import (
    require_full_staff_user,
    require_internal_staff_user,
    require_store_user,
    resolve_account_role,
)
from .domain.roles import AccountRole, get_role_spec
from .forms import StaffAccountCreateForm, StoreAccountCreateForm
from .read.selectors import (
    count_staff_open_orders,
    count_staff_unprocessed_partner_requests,
    get_store_portal_snapshot,
    list_staff_open_orders,
    list_staff_unprocessed_partner_requests,
    public_store_locator_entries,
)
from .write.dispatch import dispatch_account_creation


def store_list(request):
    return render(
        request,
        "accounts/store_list.html",
        {"stores": public_store_locator_entries()},
    )


@login_required
def portal(request):
    role = resolve_account_role(request.user)
    role_spec = get_role_spec(role)

    if role_spec.portal_route is None:
        return render(
            request,
            "accounts/no_store_connected.html",
            status=403,
        )

    return redirect(role_spec.portal_route)


@login_required
def store_portal(request):
    store = require_store_user(request)
    context = get_store_portal_snapshot(store)

    return render(
        request,
        "accounts/store_portal.html",
        context,
    )


@login_required
def restricted_staff_portal(request):
    require_internal_staff_user(request)

    if resolve_account_role(request.user) != AccountRole.RESTRICTED_STAFF:
        return render(
            request,
            "accounts/no_store_connected.html",
            status=403,
        )

    context = {
        "open_orders": list_staff_open_orders(limit=10),
        "unprocessed_partner_requests": list_staff_unprocessed_partner_requests(limit=10),
        "open_order_count": count_staff_open_orders(),
        "unprocessed_partner_request_count": count_staff_unprocessed_partner_requests(),
    }

    return render(
        request,
        "accounts/restricted_staff_portal.html",
        context,
    )


@login_required
def staff_portal(request):
    require_full_staff_user(request)

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


@login_required
def account_create_choice(request):
    require_full_staff_user(request)
    return render(request, "accounts/account_create_choice.html")


@login_required
def create_store_account_view(request):
    require_full_staff_user(request)

    if request.method == "POST":
        form = StoreAccountCreateForm(request.POST)
        if form.is_valid():
            store = dispatch_account_creation(form.to_command())
            messages.success(
                request,
                f"Store account created for {store.name}.",
            )
            return redirect("accounts:staff_portal")
    else:
        form = StoreAccountCreateForm()

    return render(
        request,
        "accounts/create_store_account.html",
        {"form": form},
    )


@login_required
def create_staff_account_view(request):
    require_full_staff_user(request)

    if request.method == "POST":
        form = StaffAccountCreateForm(request.POST)
        if form.is_valid():
            staff_account = dispatch_account_creation(form.to_command())
            messages.success(
                request,
                f"Staff account created for {staff_account.user.username}.",
            )
            return redirect("accounts:staff_portal")
    else:
        form = StaffAccountCreateForm()

    return render(
        request,
        "accounts/create_staff_account.html",
        {"form": form},
    )
