from __future__ import annotations

from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import Resolver404, resolve

from accounts.roles import AccountRole
from config.policies import (
    AUTH_EXEMPT_VIEWS,
    EXEMPT_PATH_PREFIXES,
    VIEW_CAPABILITIES,
)


class LoginRequiredMiddleware:
    """Require authentication for protected application views.

    Global route exemptions are composed in config.policies.

    Django authentication views such as login and password reset must be
    reachable before login. Auth-exempt does not necessarily mean public:
    views such as password_change may still enforce authentication themselves.

    Inactive authenticated sessions are logged out and redirected to the
    inactive-account information page.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if not request.user.is_active:
                logout(request)
                return redirect("accounts:inactive")

            return self.get_response(request)

        if self._is_exempt_path(request.path_info):
            return self.get_response(request)

        if self._is_auth_exempt_view(request.path_info):
            return self.get_response(request)

        return redirect_to_login(
            request.get_full_path(),
            settings.LOGIN_URL,
            "next",
        )

    @staticmethod
    def _is_exempt_path(path: str) -> bool:
        exempt_prefixes = (
            LoginRequiredMiddleware._path_from_url(settings.LOGIN_URL),
            "/accounts/login/",
            "/accounts/logout/",
            "/admin/",
            settings.STATIC_URL,
            getattr(settings, "MEDIA_URL", ""),
            "/favicon.ico",
        )

        return any(
            prefix and path.startswith(prefix)
            for prefix in exempt_prefixes
        )

    @staticmethod
    def _is_auth_exempt_view(path: str) -> bool:
        try:
            resolver_match = resolve(path)
        except Resolver404:
            return False

        return resolver_match.view_name in AUTH_EXEMPT_VIEWS

    @staticmethod
    def _path_from_url(url: str) -> str:
        parsed_url = urlparse(url)

        return parsed_url.path or url


class ViewCapabilityMiddleware:
    """Deny access unless the resolved view has an explicit access policy.

    Access policy is composed centrally in config.policies.

    Rules:

        - exempt paths are ignored
        - auth-exempt views are allowed through this middleware
        - protected views require a capability
        - views missing from policy are denied
        - missing or false capabilities are denied
        - anonymous users are redirected to login for protected views

    Auth-exempt does not always mean public. Some Django auth views, such as
    password_change, enforce their own login requirement.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.path.startswith(EXEMPT_PATH_PREFIXES):
            return None

        resolver_match = getattr(request, "resolver_match", None)

        if resolver_match is None:
            raise PermissionDenied("Could not resolve access policy for this request.")

        view_name = resolver_match.view_name

        if view_name in AUTH_EXEMPT_VIEWS:
            return None

        required_capability = VIEW_CAPABILITIES.get(view_name)

        if required_capability is None:
            raise PermissionDenied("This view does not declare an access policy.")

        if not request.user.is_authenticated:
            return redirect_to_login(
                request.get_full_path(),
                login_url=settings.LOGIN_URL,
            )

        role_spec = getattr(request, "role_spec", None)

        if role_spec is None:
            raise PermissionDenied("Account role context is missing.")

        if not role_spec.allows(required_capability):
            raise PermissionDenied("You do not have permission to access this page.")

        return None


class ShopDetailsRequiredMiddleware:
    """A shop invited by mail fills in its details before anything else.

    Until its customer record has phone, city and address (is_complete), a
    business customer's portal pages lead to the store form: we need to
    know where to deliver before they can order. Public pages, the store
    form itself and the auth pages stay open. Runs after
    ViewCapabilityMiddleware, so the role is known and denied pages are
    already refused.
    """

    ALLOWED_VIEWS = frozenset(
        {
            "business_portal:edit_store",
        }
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if getattr(request, "account_role", None) != AccountRole.BUSINESS_CUSTOMER:
            return None

        resolver_match = getattr(request, "resolver_match", None)

        if resolver_match is None:
            return None

        view_name = resolver_match.view_name

        if (
            not view_name.startswith("business_portal:")
            or view_name in self.ALLOWED_VIEWS
        ):
            return None

        membership = getattr(request.user, "customer_membership", None)

        if membership is None or membership.customer.is_complete:
            return None

        return redirect("business_portal:edit_store")
