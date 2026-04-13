from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404

from ..models import Order


def _with_order_summary(queryset):
    """
    Add common order summary annotations used across portal and history reads.

    These derived fields keep templates simpler and avoid repeating the same
    aggregate logic in multiple selectors.
    """
    return queryset.annotate(
        line_count=Count("items"),
        total_boxes=Coalesce(Sum("items__boxes"), 0),
    )


def _staff_orders_queryset():
    """
    Base queryset for staff-visible order lists.

    Staff-facing order reads usually need:
    - store joined in one query
    - common summary annotations

    Keeping that shared shape here avoids noisy repetition in multiple selectors.
    """
    return _with_order_summary(
        Order.objects.select_related("store")
    )


def latest_order_for_store(store):
    return (
        store.orders
        .prefetch_related("items")
        .order_by("-created_at")
        .first()
    )


def list_store_orders(store):
    return (
        _with_order_summary(store.orders)
        .order_by("-created_at")
    )


def list_active_orders_for_store(store):
    """
    Return current non-delivered, non-cancelled orders for one store.

    This is used by the store portal home where only currently relevant
    orders should be shown.
    """
    return (
        _with_order_summary(store.orders)
        .exclude(status__in=[Order.Status.DELIVERED, Order.Status.CANCELLED])
        .order_by("-created_at")
    )


def get_order_for_store(store, order_id):
    return get_object_or_404(
        _with_order_summary(
            store.orders.prefetch_related("items")
        ),
        pk=order_id,
    )


def list_pending_orders_for_staff():
    """
    Return pending orders for the restricted/full staff operations portal.

    Orders are sorted oldest first so staff can work through the queue in a
    predictable order.
    """
    return list(
        _staff_orders_queryset()
        .filter(status=Order.Status.PENDING)
        .order_by("created_at")
    )


def list_packed_orders_for_staff():
    """
    Return packed orders for the restricted/full staff operations portal.

    Packed orders are sorted by packed timestamp first, then by creation time,
    oldest first, to support delivery follow-up.
    """
    return list(
        _staff_orders_queryset()
        .filter(status=Order.Status.PACKED)
        .order_by("packed_at", "created_at")
    )


def _staff_order_history_base_queryset():
    """
    Base queryset for historical staff-visible orders.

    History includes only closed orders:
    - delivered
    - cancelled
    """
    return (
        _staff_orders_queryset()
        .filter(status__in=[Order.Status.DELIVERED, Order.Status.CANCELLED])
    )


def list_order_history_for_staff(*, status_filter: str = "all", sort: str = "date"):
    """
    Return historical staff-visible orders.

    Supported status filters:
    - all
    - delivered
    - cancelled

    Supported sort options:
    - date

    The default "all" view interleaves delivered and cancelled orders naturally
    by date instead of grouping by status first.
    """
    queryset = _staff_order_history_base_queryset()

    status_dispatch = {
        "all": lambda qs: qs,
        "delivered": lambda qs: qs.filter(status=Order.Status.DELIVERED),
        "cancelled": lambda qs: qs.filter(status=Order.Status.CANCELLED),
    }

    sort_dispatch = {
        "date": lambda qs: qs.order_by("-created_at"),
    }

    apply_status_filter = status_dispatch.get(status_filter, status_dispatch["all"])
    apply_sort = sort_dispatch.get(sort, sort_dispatch["date"])

    queryset = apply_status_filter(queryset)
    queryset = apply_sort(queryset)

    return list(queryset)


def count_pending_orders_for_staff() -> int:
    return Order.objects.filter(status=Order.Status.PENDING).count()


def count_packed_orders_for_staff() -> int:
    return Order.objects.filter(status=Order.Status.PACKED).count()


def get_order_for_staff(order_id):
    """
    Return one order for internal staff work.

    Unlike store detail reads, this selector is not store-scoped because staff
    work across stores.
    """
    return get_object_or_404(
        _with_order_summary(
            Order.objects
            .select_related("store")
            .prefetch_related("items")
        ),
        pk=order_id,
    )
