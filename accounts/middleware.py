from __future__ import annotations

from django.core.exceptions import PermissionDenied

from accounts.errors import InvalidAccountIdentity
from accounts.permissions import resolve_account_role
from accounts.roles import get_role_spec


class AccountContextMiddleware:
    """Attach business account role context to each request.

    Django authentication answers:

        Who is logged in?

    The accounts app answers:

        What business identity does that user represent?

    This middleware makes the resolved account role and role spec available on
    the request so views, navigation and access policy can make consistent
    decisions.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            request.account_role = resolve_account_role(request.user)
        except InvalidAccountIdentity as error:
            raise PermissionDenied("Invalid account identity.") from error

        request.role_spec = get_role_spec(request.account_role)

        return self.get_response(request)
