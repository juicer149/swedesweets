from accounts.models import Store
from ordering.read.selectors import (
    list_active_orders_for_store,
    list_packed_orders_for_staff,
    list_pending_orders_for_staff,
)
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
    """
    Read model for the store portal homepage.
    """
    return {
        "store": store,
        "active_orders": list_active_orders_for_store(store),
    }


def get_restricted_staff_portal_snapshot() -> dict:
    """
    Read model for the restricted staff operations portal.

    Restricted staff focus on operational order handling only.
    """
    return {
        "pending_orders": list_pending_orders_for_staff(),
        "packed_orders": list_packed_orders_for_staff(),
    }


def get_full_staff_portal_snapshot() -> dict:
    """
    Read model for the full staff portal.

    Full staff see the same operational order overview as restricted staff,
    plus incoming partner requests for broader administrative work.
    """
    return {
        "pending_orders": list_pending_orders_for_staff(),
        "packed_orders": list_packed_orders_for_staff(),
        "unprocessed_partner_requests": list_staff_unprocessed_partner_requests(limit=10),
        "unprocessed_partner_request_count": count_staff_unprocessed_partner_requests(),
    }


def list_staff_unprocessed_partner_requests(*, limit: int = 10):
    return list(
        PartnerRequest.objects
        .filter(is_processed=False)
        .order_by("-created_at")[:limit]
    )


def count_staff_unprocessed_partner_requests() -> int:
    return PartnerRequest.objects.filter(is_processed=False).count()
