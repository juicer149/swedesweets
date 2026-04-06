from django.contrib import admin

from .models import PartnerRequest


@admin.register(PartnerRequest)
class PartnerRequestAdmin(admin.ModelAdmin):
    """
    Admin review surface for public partner requests.

    DESIGN:
    - Admin reviews requests manually
    - Admin may mark them handled/unhandled
    - This admin does not create accounts or stores

    Why:
    - keeps public inbound data separate from internal provisioning
    - avoids privileged side effects in admin bulk actions
    """

    list_display = (
        "store_name",
        "name",
        "email",
        "phone",
        "is_processed",
        "created_at",
        "processed_at",
    )
    list_filter = (
        "is_processed",
        "created_at",
    )
    search_fields = (
        "store_name",
        "name",
        "email",
        "phone",
        "address",
        "message",
        "admin_notes",
    )
    readonly_fields = (
        "created_at",
        "processed_at",
    )
    ordering = ("-created_at",)

    fieldsets = (
        (
            "Partner contact",
            {
                "fields": (
                    "name",
                    "store_name",
                    "email",
                    "phone",
                    "address",
                    "message",
                )
            },
        ),
        (
            "Review",
            {
                "fields": (
                    "is_processed",
                    "processed_at",
                    "admin_notes",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": ("created_at",),
            },
        ),
    )

    actions = (
        "mark_processed",
        "mark_unprocessed",
    )

    @admin.action(description="Mark selected requests as processed")
    def mark_processed(self, request, queryset):
        for obj in queryset:
            obj.mark_processed()

    @admin.action(description="Mark selected requests as unprocessed")
    def mark_unprocessed(self, request, queryset):
        for obj in queryset:
            obj.mark_unprocessed()
