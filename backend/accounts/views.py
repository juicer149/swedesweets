from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import Store


def store_list(request):
    """Shows a list of all active Stores with an address."""

    stores = (
        Store.objects
        .filter(is_active=True)
        .exclude(address__isnull=True)
        .exclude(address="")
        .order_by("name")
    )

    return render(request, "accounts/store_list.html", {
        "stores": stores
        })


@login_required
def portal(request):
    """
    Authenticated entry point.

    Shows the Store connected to the logged-in user.
    """

    store = getattr(request.user, "store", None)

    return render(
        request,
        "accounts/portal.html",
        {"store": store},
    )

