from accounts.models import Store
from ordering.read.selectors import latest_order_for_store
from ordering.models import Order
from partner_request.models import PartnerRequest


def public_store_locator_entries():
    return (
        Store.objects
        .filter(is_active=True)
        .exclude(address__isnull=True)
        .exclude(address="")
        .order_by("name")
        .values("id", "name", "address")
    )


def get_store_portal_snapshot(store: Store) -> dict:
    return {
        "store": store,
        "last_order": latest_order_for_store(store),
    }


def list_staff_open_orders(*, limit: int = 10):
    return list(
        Order.objects
        .exclude(status=Order.Status.DELIVERED)
        .select_related("store")
        .order_by("-created_at")[:limit]
    )


def count_staff_open_orders() -> int:
    return Order.objects.exclude(status=Order.Status.DELIVERED).count()


def list_staff_unprocessed_partner_requests(*, limit: int = 10):
    return list(
        PartnerRequest.objects
        .filter(is_processed=False)
        .order_by("-created_at")[:limit]
    )


def count_staff_unprocessed_partner_requests() -> int:
    return PartnerRequest.objects.filter(is_processed=False).count()
