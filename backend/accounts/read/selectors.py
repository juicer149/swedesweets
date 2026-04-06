from accounts.models import Store
from ordering.models import Order
from ordering.read.selectors import latest_order_for_store
from partner_request.models import PartnerRequest


def public_store_locator_entries():
    """
    Return stores suitable for the public 'Find sweets' page.

    This is a read selector, not business logic:
    - only active stores are shown
    - stores must have a usable address
    - results are ordered for stable display

    The selector returns a lightweight read projection instead of exposing
    full model instances to the template layer when only public display data
    is needed.
    """
    return (
        Store.objects
        .filter(is_active=True)
        .exclude(address__isnull=True)
        .exclude(address="")
        .order_by("name")
        .values("id", "name", "address")
    )


def get_store_portal_snapshot(store):
    """
    Return minimal read data for the store portal.

    This currently exposes the latest order only, but exists as a selector so
    the view does not need to know how store-facing read data is assembled.
    """
    last_order = None
    if store.is_active:
        last_order = latest_order_for_store(store)

    return {
        "store": store,
        "last_order": last_order,
    }


def list_staff_open_orders(*, limit: int = 10):
    """
    Return recent open orders for the internal staff portal.

    Open orders are all orders that are not yet delivered.
    """
    return (
        Order.objects
        .exclude(status=Order.Status.DELIVERED)
        .select_related("store", "store__user")
        .order_by("-created_at")[:limit]
    )


def count_staff_open_orders() -> int:
    """
    Return the number of currently open orders.
    """
    return Order.objects.exclude(status=Order.Status.DELIVERED).count()


def list_staff_unprocessed_partner_requests(*, limit: int = 10):
    """
    Return recent unprocessed partner requests for the internal staff portal.
    """
    return (
        PartnerRequest.objects
        .filter(is_processed=False)
        .order_by("-created_at")[:limit]
    )


def count_staff_unprocessed_partner_requests() -> int:
    """
    Return the number of currently unprocessed partner requests.
    """
    return PartnerRequest.objects.filter(is_processed=False).count()
