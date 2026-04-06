from django.contrib import admin
from django.utils import timezone

from .models import PartnerRequest


@admin.register(PartnerRequest)
class PartnerRequestAdmin(admin.ModelAdmin):
    """
    Admin review surface for public partner requests.

    DESIGN:
    - Admin reviews requests manually
    - Admin may mark them handled/unhandled
    - This admin does not create accounts or stores

    WHY:
    - keeps public inbound data separate from internal provisioning
    - avoids privileged side effects in admin bulk actions
    - makes lead follow-up easy without turning this into an onboarding engine
    """

    list_display = (
        "store_name",
        "name",
        "email",
        "phone",
        "is_processed",
        "created_at",
        "processed_at",
        "short_message",
    )
    list_filter = (
        "is_processed",
        "created_at",
        "processed_at",
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
    ordering = ("is_processed", "-created_at")

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

    @admin.display(description="Message")
    def short_message(self, obj: PartnerRequest) -> str:
        if not obj.message:
            return "-"
        text = obj.message.strip()
        if len(text) <= 60:
            return text
        return f"{text[:57]}..."

    @admin.action(description="Mark selected requests as processed")
    def mark_processed(self, request, queryset):
        for obj in queryset:
            obj.mark_processed()

    @admin.action(description="Mark selected requests as unprocessed")
    def mark_unprocessed(self, request, queryset):
        for obj in queryset:
            obj.mark_unprocessed()

    def save_model(self, request, obj, form, change):
        """
        Keep processed_at consistent when is_processed is edited directly
        through the admin form instead of bulk actions.
        """
        if obj.is_processed and obj.processed_at is None:
            obj.processed_at = timezone.now()

        if not obj.is_processed:
            obj.processed_at = None

        super().save_model(request, obj, form, change)
