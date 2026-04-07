from django.core.exceptions import PermissionDenied


def is_store_user(user) -> bool:
    """
    Return True if the authenticated user is linked to a Store.

    In the current system, a store user is an external partner account that
    places orders through the store portal.

    Current rule:
    - authenticated
    - has a linked `store`
    """
    if not user.is_authenticated:
        return False
    return hasattr(user, "store")


def is_staff_user(user) -> bool:
    """
    Return True if the authenticated user is an internal staff account.

    Staff users represent internal company users rather than partner stores.

    Current rule:
    - authenticated
    - `is_staff=True`
    """
    return bool(user.is_authenticated and user.is_staff)


def require_store_user(request):
    """
    Require that the authenticated request user is a store user.

    Returns the linked Store object on success.

    Raises:
        PermissionDenied: if the authenticated user is not linked to a Store.
    """
    store = getattr(request.user, "store", None)
    if store is None:
        raise PermissionDenied("This page is only available to store accounts.")
    return store


def require_staff_user(request) -> None:
    """
    Require that the authenticated request user is an internal staff user.

    Raises:
        PermissionDenied: if the authenticated user is not a staff account.
    """
    if not is_staff_user(request.user):
        raise PermissionDenied("This page is only available to staff accounts.")
