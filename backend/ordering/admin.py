from django.contrib import admin

from .models import (
    FulfilledOrder,
    FulfilledOrderItem,
    RequestedOrder,
    RequestedOrderItem,
)


class RequestedOrderItemInline(admin.TabularInline):
    model = RequestedOrderItem
    extra = 0


@admin.register(RequestedOrder)
class RequestedOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "store", "created_at")
    list_filter = ("created_at",)
    search_fields = ("id", "store__name", "store__user__username")
    inlines = [RequestedOrderItemInline]


class FulfilledOrderItemInline(admin.TabularInline):
    model = FulfilledOrderItem
    extra = 0


@admin.register(FulfilledOrder)
class FulfilledOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "requested_order", "packed_at", "delivered_at")
    list_filter = ("packed_at", "delivered_at")
    search_fields = ("id", "requested_order__id", "requested_order__store__name")
    inlines = [FulfilledOrderItemInline]
