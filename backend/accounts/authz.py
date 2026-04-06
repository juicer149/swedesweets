from django.core.exceptions import PermissionDenied


def is_store_user(user) -> bool:
    """
    Return True if the user is linked to a Store.

    In the current system, store users are external partner accounts that
    place orders through the store portal.
    """
    if not user.is_authenticated:
        return False
    return hasattr(user, "store")


def is_staff_user(user) -> bool:
    """
    Return True if the user is an internal staff account.

    Staff users represent internal company users rather than partner stores.
    """
    return bool(user.is_authenticated and user.is_staff)


def require_store_user(request):
    """
    Require that the authenticated request user is a store user.

    Returns the linked Store object on success.
    """
    store = getattr(request.user, "store", None)
    if store is None:
        raise PermissionDenied("This page is only available to store accounts.")
    return store


def require_staff_user(request) -> None:
    """
    Require that the authenticated request user is an internal staff user.
    """
    if not is_staff_user(request.user):
        raise PermissionDenied("This page is only available to staff accounts.")
