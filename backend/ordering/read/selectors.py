from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404

from ordering.models import Order


def latest_order_for_store(store):
    return (
        store.orders
        .prefetch_related("items")
        .order_by("-created_at")
        .first()
    )


def list_store_orders(store):
    return (
        store.orders
        .annotate(
            line_count=Count("items"),
            total_boxes=Coalesce(Sum("items__boxes"), 0),
        )
        .order_by("-created_at")
    )


def list_active_orders_for_store(store):
    """
    Return active (not delivered) orders for one store.

    This selector is intended for the store portal homepage, where we want
    a short operational overview of orders that are still in progress.
    """
    return (
        store.orders
        .exclude(status=Order.Status.DELIVERED)
        .annotate(
            line_count=Count("items"),
            total_boxes=Coalesce(Sum("items__boxes"), 0),
        )
        .order_by("-created_at")
    )


def get_order_for_store(store, order_id):
    return get_object_or_404(
        store.orders
        .prefetch_related("items")
        .annotate(
            line_count=Count("items"),
            total_boxes=Coalesce(Sum("items__boxes"), 0),
        ),
        pk=order_id,
    )
