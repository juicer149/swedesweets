from django.core.validators import MaxLengthValidator
from django.db import models
from django.utils import timezone


class PartnerRequest(models.Model):
    """
    Public inbound lead from a potential retail partner.

    DESIGN:
    - This is a boundary model, not an internal business entity.
    - It stores external contact data from a public form.
    - It does not create users, stores, or permissions.
    - Internal onboarding remains an explicit manual admin action outside this app.

    RESPONSIBILITY:
    - Persist incoming partner interest safely
    - Normalize identity-like input where useful (email)
    - Track whether admin has handled the request

    NON-RESPONSIBILITY:
    - Approval/rejection workflows tied to provisioning
    - Auth/account creation
    - Store lifecycle management
    """

    name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Name of the contact person.",
    )
    store_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Name of the interested store or retailer.",
    )
    email = models.EmailField(
        db_index=True,
        help_text="Primary contact email address.",
    )
    phone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional phone number.",
    )
    address = models.CharField(
        max_length=500,
        blank=True,
        help_text="Optional store address.",
    )
    message = models.TextField(
        blank=True,
        validators=[MaxLengthValidator(2000)],
        help_text="Optional free-text message.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    is_processed = models.BooleanField(
        default=False,
        help_text="Whether admin has handled this request.",
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the request was marked as handled.",
    )
    admin_notes = models.TextField(
        blank=True,
        validators=[MaxLengthValidator(2000)],
        help_text="Internal notes for admin use only.",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Partner request"
        verbose_name_plural = "Partner requests"

    def save(self, *args, **kwargs):
        """
        Normalize email at the persistence boundary.

        Why here:
        - keeps storage consistent regardless of form/admin entry path
        - avoids casing bugs in admin search and manual review
        """
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def mark_processed(self) -> None:
        """
        Mark the request as handled.

        This is intentionally small and local:
        - it only updates the request's own state
        - it does not trigger provisioning side effects
        """
        if self.is_processed:
            return

        self.is_processed = True
        self.processed_at = timezone.now()
        self.save(update_fields=["is_processed", "processed_at"])

    def mark_unprocessed(self) -> None:
        """
        Re-open the request for admin review.

        Useful when a request was marked handled by mistake.
        """
        if not self.is_processed:
            return

        self.is_processed = False
        self.processed_at = None
        self.save(update_fields=["is_processed", "processed_at"])

    def __str__(self) -> str:
        label = self.store_name or self.name or "Unknown partner request"
        return f"{label} ({self.email})"
