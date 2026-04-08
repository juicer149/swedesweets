from django.core.exceptions import PermissionDenied

from .domain.errors import InvalidAccountIdentity
from .domain.roles import AccountRole, StaffAccessLevel


def is_store_user(user) -> bool:
    """
    Return True if the authenticated user is linked to a Store.

    NOTE:
    This helper answers only the narrow question "does this user have a Store
    relation?" It does not by itself prove that the overall account identity is
    valid. Full role resolution belongs in resolve_account_role().
    """
    if not user.is_authenticated:
        return False
    return hasattr(user, "store")


def is_internal_staff_user(user) -> bool:
    """
    Return True if the authenticated user is linked to a StaffAccount.

    NOTE:
    This helper does not validate exclusivity against Store. Full business-role
    validation belongs in resolve_account_role().
    """
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
    Resolve the business-level account role for an authenticated user.

    VALID STATES:
    - Store-linked user -> STORE
    - StaffAccount-linked user with restricted access -> RESTRICTED_STAFF
    - StaffAccount-linked user with full access -> FULL_STAFF
    - authenticated user with no business identity -> UNKNOWN
    - anonymous user -> UNKNOWN

    IMPORTANT DESIGN DECISION:
    A Django User must never represent two business identities at once.

    In particular, a user may not be linked to both:
    - Store
    - StaffAccount

    If that invalid state appears, this function raises InvalidAccountIdentity
    instead of silently choosing one side. This is intentional.

    WHY:
    - Silent priority rules hide corrupt data
    - Store and staff are different actors with different permissions and
      different work surfaces
    - Failing loudly is safer than accidentally routing a user into the wrong
      portal

    This keeps role resolution deterministic and makes invalid identity data
    visible immediately.
    """
    if not user.is_authenticated:
        return AccountRole.UNKNOWN

    has_store = hasattr(user, "store")
    has_staff_account = hasattr(user, "staff_account")

    if has_store and has_staff_account:
        raise InvalidAccountIdentity(
            "A user cannot be linked to both Store and StaffAccount."
        )

    if has_staff_account:
        access_level = user.staff_account.access_level

        if access_level == StaffAccessLevel.RESTRICTED:
            return AccountRole.RESTRICTED_STAFF

        if access_level == StaffAccessLevel.FULL:
            return AccountRole.FULL_STAFF

        raise InvalidAccountIdentity(
            f"Unknown staff access level: {access_level!r}"
        )

    if has_store:
        return AccountRole.STORE

    return AccountRole.UNKNOWN


def require_store_user(request):
    """
    Require that the authenticated request user is a store user.

    Returns the linked Store object on success.
    """
    store = getattr(request.user, "store", None)
    if store is None:
        raise PermissionDenied("This page is only available to store accounts.")
    return store


def require_internal_staff_user(request):
    """
    Require that the authenticated request user is an internal staff user.

    Returns the linked StaffAccount on success.
    """
    staff_account = getattr(request.user, "staff_account", None)
    if staff_account is None:
        raise PermissionDenied("This page is only available to internal staff accounts.")
    return staff_account


def require_restricted_staff_user(request):
    """
    Require that the authenticated request user is a restricted staff user.

    Returns the linked StaffAccount on success.
    """
    staff_account = require_internal_staff_user(request)
    if staff_account.access_level != StaffAccessLevel.RESTRICTED:
        raise PermissionDenied("This page is only available to restricted staff accounts.")
    return staff_account


def require_full_staff_user(request):
    """
    Require that the authenticated request user is a full staff user.

    Returns the linked StaffAccount on success.
    """
    staff_account = require_internal_staff_user(request)
    if staff_account.access_level != StaffAccessLevel.FULL:
        raise PermissionDenied("This page is only available to full staff accounts.")
    return staff_account
