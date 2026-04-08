from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .authz import (
    require_full_staff_user,
    require_restricted_staff_user,
    require_store_user,
    resolve_account_role,
)
from .domain.errors import InvalidAccountIdentity
from .domain.roles import get_role_spec
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

    Dispatch is based on resolved business role, not just Django admin flags.

    DESIGN DECISION:
    Role resolution is intentionally strict. If the authenticated user has an
    invalid business-identity combination, such as being linked to both Store
    and StaffAccount, the system treats that as configuration error rather than
    silently choosing one side.

    WHY:
    - store users, restricted staff, and full staff are different actors
    - they belong in different work surfaces
    - silent fallback would hide bad data
    - failing closed is safer than routing a user into the wrong portal
    """
    try:
        role = resolve_account_role(request.user)
    except InvalidAccountIdentity:
        return render(
            request,
            "accounts/no_store_connected.html",
            status=403,
        )

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
    """
    Portal for store-linked partner accounts.

    Responsibility:
    - resolve the Store linked to the authenticated user
    - show store-facing overview data
    - act as entrypoint into ordering

    Non-responsibility:
    - internal staff operations
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
def restricted_staff_portal(request):
    """
    Portal for restricted internal staff.

    Restricted staff are internal operational users who should work through the
    portal only and should not require Django admin access.

    DESIGN DECISION:
    This view is guarded directly by require_restricted_staff_user() instead of
    combining a broader staff check with extra branching in the view. That keeps
    access control explicit and centralized in authz helpers.
    """
    require_restricted_staff_user(request)

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
    """
    Portal for full internal staff.

    Full staff users may:
    - monitor operational work
    - create new store and staff accounts
    - access Django admin for deeper maintenance
    """
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
    """
    Entry page for full-staff account provisioning.

    Only full staff may provision new internal or store-linked accounts.
    """
    require_full_staff_user(request)
    return render(request, "accounts/account_create_choice.html")


@login_required
def create_store_account_view(request):
    """
    Create a new store-linked account through the explicit provisioning flow.

    HTTP input is validated by the form and then converted into a typed command
    before dispatching into the write layer.
    """
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
    """
    Create a new internal staff account through the explicit provisioning flow.

    The chosen access level determines whether the created staff account is
    restricted or full.
    """
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
