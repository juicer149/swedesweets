from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from config.login_routing import get_after_login_redirect_name


def index(request: HttpRequest) -> HttpResponse:
    """Redirect the site root to the public storefront catalog.

    A placeholder landing page: the public-site branch may later replace
    this with a real hero page, but storefront:product_list remains the
    canonical catalog URL either way, so nothing downstream needs to
    change when that happens.
    """

    return redirect("storefront:product_list")


@login_required
def after_login(request):
    return redirect(
        get_after_login_redirect_name(
            account_role=request.account_role,
            role_spec=request.role_spec,
        )
    )
