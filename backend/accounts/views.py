from django.shortcuts import render

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


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
