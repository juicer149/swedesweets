from __future__ import annotations

from types import SimpleNamespace

import pytest
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory

from accounts.middleware import (
    AccountContextMiddleware,
)
from accounts.models import CustomerMembership, StaffAccount
from accounts.roles import AccountRole, Capability, StaffAccessLevel
from accounts.tests.factories import (
    customer_membership_factory,
    full_staff_user_factory,
    restricted_staff_user_factory,
    superuser_factory,
    user_factory,
)
from customers.tests.factories import customer_factory


def _middleware_response(request):
    return request


def _build_request(*, user, path: str = "/", view_name: str = "index"):
    request = RequestFactory().get(path)
    request.user = user
    request.resolver_match = SimpleNamespace(view_name=view_name)
    return request


def _attach_account_context(request):
    middleware = AccountContextMiddleware(_middleware_response)
    return middleware(request)


@pytest.mark.django_db
def test_account_context_middleware_attaches_owner_role_context():
    request = _build_request(
        user=superuser_factory(),
        view_name="index",
    )

    response_request = _attach_account_context(request)

    assert response_request.account_role == AccountRole.OWNER
    assert response_request.role_spec.allows(Capability.VIEW_STAFF_OPS)
    assert response_request.role_spec.allows(Capability.MANAGE_ACCOUNTS)


@pytest.mark.django_db
def test_account_context_middleware_attaches_full_staff_role_context():
    request = _build_request(
        user=full_staff_user_factory(),
        view_name="index",
    )

    response_request = _attach_account_context(request)

    assert response_request.account_role == AccountRole.FULL_STAFF
    assert response_request.role_spec.allows(Capability.VIEW_STAFF_OPS)
    assert response_request.role_spec.allows(Capability.EDIT_PRODUCTS)


@pytest.mark.django_db
def test_account_context_middleware_attaches_restricted_staff_role_context():
    request = _build_request(
        user=restricted_staff_user_factory(),
        view_name="index",
    )

    response_request = _attach_account_context(request)

    assert response_request.account_role == AccountRole.RESTRICTED_STAFF
    assert response_request.role_spec.allows(Capability.VIEW_STAFF_OPS)
    assert response_request.role_spec.allows(Capability.PACK_ORDERS)
    assert not response_request.role_spec.allows(Capability.EDIT_PRODUCTS)


@pytest.mark.django_db
def test_account_context_middleware_attaches_customer_role_context():
    user = user_factory(username="customer@example.com")
    customer = customer_factory()

    customer_membership_factory(
        user=user,
        customer=customer,
    )

    request = _build_request(
        user=user,
        view_name="index",
    )

    response_request = _attach_account_context(request)

    assert response_request.account_role == AccountRole.BUSINESS_CUSTOMER
    assert response_request.role_spec.allows(Capability.VIEW_BUSINESS_PORTAL)
    assert not response_request.role_spec.allows(Capability.VIEW_STAFF_OPS)


@pytest.mark.django_db
def test_account_context_middleware_attaches_unknown_role_context():
    request = _build_request(
        user=user_factory(username="unknown@example.com"),
        view_name="index",
    )

    response_request = _attach_account_context(request)

    assert response_request.account_role == AccountRole.UNKNOWN
    assert not response_request.role_spec.allows(Capability.VIEW_STAFF_OPS)
    assert not response_request.role_spec.allows(Capability.VIEW_BUSINESS_PORTAL)


@pytest.mark.django_db
def test_account_context_middleware_rejects_invalid_account_identity():
    user = user_factory(username="invalid@example.com")
    customer = customer_factory()

    StaffAccount.objects.create(
        user=user,
        access_level=StaffAccessLevel.RESTRICTED,
    )
    CustomerMembership.objects.create(
        user=user,
        customer=customer,
    )

    request = _build_request(
        user=user,
        view_name="index",
    )

    with pytest.raises(PermissionDenied):
        _attach_account_context(request)
