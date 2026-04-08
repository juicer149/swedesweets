from django.core.exceptions import PermissionDenied

from .domain.roles import AccountRole, StaffAccessLevel


def is_store_user(user) -> bool:
    if not user.is_authenticated:
        return False
    return hasattr(user, "store")


def is_internal_staff_user(user) -> bool:
    if not user.is_authenticated:
        return False
    return hasattr(user, "staff_account")


def is_restricted_staff_user(user) -> bool:
    if not is_internal_staff_user(user):
        return False
    return user.staff_account.access_level == StaffAccessLevel.RESTRICTED


def is_full_staff_user(user) -> bool:
    if not is_internal_staff_user(user):
        return False
    return user.staff_account.access_level == StaffAccessLevel.FULL


def resolve_account_role(user) -> AccountRole:
    """
    Resolve the business-level account role.

    Order matters:
    - Store users are external partner accounts
    - Staff accounts are internal operational accounts
    - Anything else is treated as unknown
    """
    if not user.is_authenticated:
        return AccountRole.UNKNOWN

    if hasattr(user, "store"):
        return AccountRole.STORE

    if hasattr(user, "staff_account"):
        if user.staff_account.access_level == StaffAccessLevel.RESTRICTED:
            return AccountRole.RESTRICTED_STAFF
        if user.staff_account.access_level == StaffAccessLevel.FULL:
            return AccountRole.FULL_STAFF

    return AccountRole.UNKNOWN


def require_store_user(request):
    store = getattr(request.user, "store", None)
    if store is None:
        raise PermissionDenied("This page is only available to store accounts.")
    return store


def require_internal_staff_user(request):
    staff_account = getattr(request.user, "staff_account", None)
    if staff_account is None:
        raise PermissionDenied("This page is only available to internal staff accounts.")
    return staff_account


def require_restricted_staff_user(request):
    staff_account = require_internal_staff_user(request)
    if staff_account.access_level != StaffAccessLevel.RESTRICTED:
        raise PermissionDenied("This page is only available to restricted staff accounts.")
    return staff_account


def require_full_staff_user(request):
    staff_account = require_internal_staff_user(request)
    if staff_account.access_level != StaffAccessLevel.FULL:
        raise PermissionDenied("This page is only available to full staff accounts.")
    return staff_account
