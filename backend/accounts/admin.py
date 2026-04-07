from django.contrib import admin

from .models import Store


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    """
    Admin surface for internal store records.

    `Store` is the trusted internal business entity for a partner retailer.

    CURRENT ROLE OF ADMIN:
    - inspect and maintain Store records
    - correct store data when needed
    - manage store activation state

    PROVISIONING NOTE:
    Account provisioning is no longer purely an admin concern. The project now
    has an explicit internal account-creation flow for creating:
    - store accounts
    - staff accounts

    Django admin still remains the deeper maintenance surface, but it is not
    the only operational path anymore.

    IMPORTANT CONCEPTUAL BOUNDARY:
    - store accounts are normal users linked to a Store
    - staff accounts are internal users with `is_staff=True`
    """

    list_display = ("name", "user", "phone", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "user__username", "user__email", "phone", "address")
    readonly_fields = ("created_at",)
    ordering = ("name",)
