from django.contrib.auth import get_user_model
from django.core.validators import MaxLengthValidator
from django.db import models, transaction

User = get_user_model()


class PartnerRequest(models.Model):
    """
    Incoming request from a potential retail partner.

    Boundary model:
    - Accepts external, messy, incomplete input
    - Normalizes and validates minimally
    - Converted manually into internal entities (User + Store)

    LIFECYCLE:
        pending  -> approved
        pending  -> rejected

    KEY DESIGN:
    - Email is identity boundary → always normalized
    - Approval is explicit (no signals, no magic)
    - Store/User are system truth
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    name = models.CharField(max_length=200, blank=True)
    store_name = models.CharField(max_length=200, blank=True)

    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=50, blank=True)

    address = models.CharField(max_length=500, blank=True)
    message = models.TextField(
        blank=True,
        validators=[MaxLengthValidator(2000)],
    )

    created_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_store = models.OneToOneField(
        "accounts.Store",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="source_request",
    )

    # -------------------------
    # Normalization
    # -------------------------

    def normalize_email(self) -> str:
        return (self.email or "").strip().lower()

    def save(self, *args, **kwargs):
        """
        Normalize email at persistence boundary.

        This guarantees:
        - No casing bugs
        - Consistent identity checks
        """
        if self.email:
            self.email = self.normalize_email()
        super().save(*args, **kwargs)

    # -------------------------
    # State helpers
    # -------------------------

    @property
    def is_pending(self) -> bool:
        return self.status == self.Status.PENDING

    @property
    def is_approved(self) -> bool:
        return self.status == self.Status.APPROVED

    @property
    def is_rejected(self) -> bool:
        return self.status == self.Status.REJECTED

    def is_ready_for_approval(self) -> bool:
        """
        Minimal business rule for MVP:
        - email
        - store_name
        - address
        """
        return bool(self.email and self.store_name and self.address)

    # -------------------------
    # Transitions
    # -------------------------

    def approve(self) -> None:
        """
        Convert PartnerRequest → User + Store.

        Guarantees:
        - Atomic operation
        - No duplicate users
        - Clean identity (email normalized)
        """

        if not self.is_pending:
            raise ValueError("Only pending requests can be approved")

        if not self.is_ready_for_approval():
            raise ValueError("Missing required data for approval")

        from accounts.models import Store

        email = self.normalize_email()

        with transaction.atomic():
            user, created = User.objects.get_or_create(
                username=email,
                defaults={
                    "email": email,
                    "first_name": self.name,
                },
            )

            if not created:
                raise ValueError("User already exists with this email")

            user.set_password("test1234")  # Need to change after testing, but good enough for MVP
            user.save(update_fields=["password"])

            store = Store.objects.create(
                user=user,
                name=self.store_name,
                phone=self.phone,
                address=self.address,
            )

            self.created_store = store
            self.status = self.Status.APPROVED
            self.save(update_fields=["created_store", "status"])

    def reject(self) -> None:
        if not self.is_pending:
            raise ValueError("Only pending requests can be rejected")

        self.status = self.Status.REJECTED
        self.save(update_fields=["status"])

    def __str__(self) -> str:
        return f"{self.store_name or 'Unknown store'} ({self.email})"
