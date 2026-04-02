from django.contrib import admin, messages
from django.contrib.auth import get_user_model

from .models import PartnerRequest

User = get_user_model()


@admin.register(PartnerRequest)
class PartnerRequestAdmin(admin.ModelAdmin):
    """
    Admin review surface for onboarding.

    Responsibilities:
    - Review external input
    - Decide approve/reject
    - Prevent invalid system states
    """

    list_display = (
        "store_name",
        "email",
        "status",
        "is_ready",
        "has_existing_user",
        "created_store",
        "created_at",
    )

    list_filter = ("status",)
    search_fields = ("store_name", "email", "name")

    readonly_fields = (
        "status",
        "created_store",
        "created_at",
    )

    actions = ("approve_requests", "reject_requests")

    ordering = ("-created_at",)

    # -------------------------
    # Display helpers
    # -------------------------

    @admin.display(boolean=True, description="Ready")
    def is_ready(self, obj: PartnerRequest) -> bool:
        return obj.is_ready_for_approval()

    @admin.display(boolean=True, description="User exists")
    def has_existing_user(self, obj: PartnerRequest) -> bool:
        return User.objects.filter(
            username=obj.email.strip().lower()
        ).exists()

    # -------------------------
    # Actions
    # -------------------------

    @admin.action(description="Approve selected requests")
    def approve_requests(self, request, queryset):
        success = 0
        failed = 0

        for obj in queryset:
            try:
                if obj.status == PartnerRequest.Status.APPROVED:
                    raise ValueError("Already approved")

                if obj.status == PartnerRequest.Status.REJECTED:
                    raise ValueError("Already rejected")

                if not obj.is_ready_for_approval():
                    raise ValueError("Missing required data")

                if User.objects.filter(
                    username=obj.email.strip().lower()
                ).exists():
                    raise ValueError(
                        "User already exists → use existing account"
                    )

                obj.approve()
                success += 1

            except Exception as exc:
                failed += 1
                self.message_user(
                    request,
                    f"[{obj.email}] {exc}",
                    level=messages.ERROR,
                )

        if success:
            self.message_user(
                request,
                f"{success} request(s) approved.",
                level=messages.SUCCESS,
            )

        if failed:
            self.message_user(
                request,
                f"{failed} request(s) failed — see errors above.",
                level=messages.WARNING,
            )

    @admin.action(description="Reject selected requests")
    def reject_requests(self, request, queryset):
        success = 0
        failed = 0

        for obj in queryset:
            try:
                if obj.status == PartnerRequest.Status.REJECTED:
                    raise ValueError("Already rejected")

                if obj.status == PartnerRequest.Status.APPROVED:
                    raise ValueError("Already approved")

                obj.reject()
                success += 1

            except Exception as exc:
                failed += 1
                self.message_user(
                    request,
                    f"[{obj.email}] {exc}",
                    level=messages.ERROR,
                )

        if success:
            self.message_user(
                request,
                f"{success} request(s) rejected.",
                level=messages.SUCCESS,
            )

        if failed:
            self.message_user(
                request,
                f"{failed} request(s) failed — see errors above.",
                level=messages.WARNING,
            )

    # -------------------------
    # Deletion control
    # -------------------------

    def delete_queryset(self, request, queryset):
        blocked = queryset.filter(status=PartnerRequest.Status.APPROVED)
        allowed = queryset.exclude(status=PartnerRequest.Status.APPROVED)

        if blocked.exists():
            self.message_user(
                request,
                "Cannot delete approved requests.",
                level=messages.ERROR,
            )

        super().delete_queryset(request, allowed)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status == PartnerRequest.Status.APPROVED:
            return False
        return super().has_delete_permission(request, obj)
