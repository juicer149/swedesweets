from django.core.exceptions import PermissionDenied


def require_request_store(request):
    store = getattr(request.user, "store", None)
    if store is None:
        raise PermissionDenied("User is not linked to a store.")
    return store


def require_active_store(store) -> None:
    if not store.is_active:
        raise PermissionDenied("Inactive stores cannot place orders.")
