from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ordering.read.selectors import latest_order_for_store

from .models import Store


def store_list(request):
    stores = (
        Store.objects
        .filter(is_active=True)
        .exclude(address__isnull=True)
        .exclude(address="")
        .order_by("name")
    )

    return render(request, "accounts/store_list.html", {"stores": stores})


@login_required
def portal(request):
    store = getattr(request.user, "store", None)

    last_order = None
    if store:
        last_order = latest_order_for_store(store)

    return render(
        request,
        "accounts/portal.html",
        {
            "store": store,
            "last_order": last_order,
        },
    )
