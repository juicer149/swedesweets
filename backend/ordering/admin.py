from django.contrib import admin
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """
    Read-only inline view of order item snapshots.

    Order items represent historical snapshots and should not be casually
    edited in admin once created.
    """

    model = OrderItem
    extra = 0
    can_delete = False
    fields = (
        "product_code",
        "product_name",
        "product_category_name",
        "product_weight_grams",
        "product_units_per_box",
        "boxes",
    )
    readonly_fields = fields
    show_change_link = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin surface for operational order handling.

    Purpose:
    - inspect incoming orders
    - filter by fulfillment status
    - update order progress with simple admin actions
    - view immutable order-item snapshots
    """

    list_display = (
        "short_id",
        "store",
        "status",
        "line_count",
        "total_boxes",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("id", "store__name", "store__user__username", "store__user__email")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    inlines = [OrderItemInline]
    actions = ("mark_pending", "mark_packed", "mark_delivered")

    fieldsets = (
        (
            "Order",
            {
                "fields": (
                    "store",
                    "status",
                    "created_at",
                )
            },
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                _line_count=Count("items"),
                _total_boxes=Coalesce(Sum("items__boxes"), 0),
            )
        )

    @admin.display(description="Order ID")
    def short_id(self, obj: Order) -> str:
        return str(obj.id)[:8]

    @admin.display(description="Products", ordering="_line_count")
    def line_count(self, obj: Order) -> int:
        return obj._line_count

    @admin.display(description="Boxes", ordering="_total_boxes")
    def total_boxes(self, obj: Order) -> int:
        return obj._total_boxes

    @admin.action(description="Mark selected orders as pending")
    def mark_pending(self, request, queryset):
        queryset.update(status=Order.Status.PENDING)

    @admin.action(description="Mark selected orders as packed")
    def mark_packed(self, request, queryset):
        queryset.update(status=Order.Status.PACKED)

    @admin.action(description="Mark selected orders as delivered")
    def mark_delivered(self, request, queryset):
        queryset.update(status=Order.Status.DELIVERED)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """
    Read-only admin view for historical order items.

    Useful for inspection and support, but order item snapshots should not
    normally be edited after creation.
    """

    list_display = (
        "order",
        "product_code",
        "product_name",
        "boxes",
        "product_category_name",
    )
    search_fields = (
        "order__id",
        "product_code",
        "product_name",
        "order__store__name",
    )
    list_filter = ("product_category_name",)
    ordering = ("-order__created_at",)
    readonly_fields = (
        "order",
        "product_code",
        "product_name",
        "product_category_name",
        "product_weight_grams",
        "product_units_per_box",
        "boxes",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
