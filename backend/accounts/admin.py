from django.contrib import admin

from .models import Store


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    """
    Admin surface for internal store records.

    Admin is the current provisioning path for stores in the MVP:
    stores are created and maintained manually by staff rather than being
    auto-created from public requests.
    """

    list_display = ("name", "user", "phone", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "user__username", "user__email", "phone", "address")
    readonly_fields = ("created_at",)
    ordering = ("name",)
