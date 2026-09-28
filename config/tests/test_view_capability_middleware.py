from __future__ import annotations

from types import SimpleNamespace

import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory

from accounts.middleware import AccountContextMiddleware
from accounts.tests.factories import (
    customer_membership_factory,
    restricted_staff_user_factory,
    superuser_factory,
    user_factory,
)
from config.middleware import ViewCapabilityMiddleware
from customers.tests.factories import customer_factory


def _middleware_response(request):
    return request


def _build_request(
    *,
    user,
    path: str = "/",
    view_name: str = "index",
):
    request = RequestFactory().get(path)
    request.user = user
    request.resolver_match = SimpleNamespace(
        view_name=view_name
    )
    return request


def _attach_account_context(request):
    middleware = AccountContextMiddleware(
        _middleware_response
    )
    return middleware(request)


def _run_view_capability_middleware(request):
    middleware = ViewCapabilityMiddleware(
        _middleware_response
    )

    return middleware.process_view(
        request,
        view_func=lambda request: request,
        view_args=(),
        view_kwargs={},
    )


@pytest.mark.django_db
def test_view_capability_middleware_allows_public_view_for_anonymous_user():
    request = _build_request(
        user=AnonymousUser(),
        path="/accounts/login/",
        view_name="login",
    )
    _attach_account_context(request)

    response = _run_view_capability_middleware(request)

    assert response is None


@pytest.mark.django_db
def test_view_capability_middleware_redirects_anonymous_user_for_protected_view():
    request = _build_request(
        user=AnonymousUser(),
        path="/ops/orders/",
        view_name="ops_orders:index",
    )
    _attach_account_context(request)

    response = _run_view_capability_middleware(request)

    assert response.status_code == 302
    assert settings.LOGIN_URL in response["Location"]
    assert "next=" in response["Location"]


@pytest.mark.django_db
def test_view_capability_middleware_allows_user_with_required_capability():
    request = _build_request(
        user=restricted_staff_user_factory(),
        path="/ops/orders/1/pack/",
        view_name="ops_orders:pack",
    )
    _attach_account_context(request)

    response = _run_view_capability_middleware(request)

    assert response is None


@pytest.mark.django_db
def test_view_capability_middleware_denies_user_without_required_capability():
    user = user_factory(username="customer@example.com")
    customer = customer_factory()

    customer_membership_factory(
        user=user,
        customer=customer,
    )

    request = _build_request(
        user=user,
        path="/ops/orders/",
        view_name="ops_orders:index",
    )
    _attach_account_context(request)

    with pytest.raises(PermissionDenied):
        _run_view_capability_middleware(request)


@pytest.mark.django_db
def test_view_capability_middleware_denies_view_without_policy():
    request = _build_request(
        user=superuser_factory(),
        path="/missing-policy/",
        view_name="missing:policy",
    )
    _attach_account_context(request)

    with pytest.raises(PermissionDenied):
        _run_view_capability_middleware(request)


@pytest.mark.django_db
def test_view_capability_middleware_exempts_admin_paths():
    request = _build_request(
        user=AnonymousUser(),
        path="/admin/",
        view_name="admin:index",
    )
    _attach_account_context(request)

    response = _run_view_capability_middleware(request)

    assert response is None
