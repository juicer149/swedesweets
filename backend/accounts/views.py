from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ordering.read.selectors import latest_order_for_store

from .read.selectors import public_store_locator_entries


def store_list(request):
    """
    Public store locator page.

    Shows active stores with a usable address so visitors can find
    retail locations that carry SwedeSweets products.
    """
    return render(
        request,
        "accounts/store_list.html",
        {"stores": public_store_locator_entries()},
    )


@login_required
def portal(request):
    """
    Partner portal landing page for the currently logged-in store user.

    Responsibility:
    - resolve the Store linked to the authenticated user
    - show a minimal portal overview
    - expose recent ordering information through read selectors

    Non-responsibility:
    - perform ordering writes
    - enforce domain rules belonging to the ordering app
    """
    store = getattr(request.user, "store", None)

    last_order = None
    if store and store.is_active:
        last_order = latest_order_for_store(store)

    return render(
        request,
        "accounts/portal.html",
        {
            "store": store,
            "last_order": last_order,
        },
    )
