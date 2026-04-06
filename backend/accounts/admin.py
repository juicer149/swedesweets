from django.contrib import admin

from .models import Store


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    """
    Admin surface for internal store records.

    Admin is still the current provisioning path for stores in the MVP:
    - create a normal Django user
    - create a Store
    - link the Store to that user

    The portal/access model now distinguishes between:
    - store accounts (linked to Store, not staff)
    - internal staff accounts (staff users, no Store required)
    """

    list_display = ("name", "user", "phone", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "user__username", "user__email", "phone", "address")
    readonly_fields = ("created_at",)
    ordering = ("name",)
