from django.conf import settings
from django.db import models

from .domain.roles import StaffAccessLevel


class Store(models.Model):
    """
    Internal, trusted representation of a retail customer.

    A Store is the business entity that participates in the system:
    it can be shown publicly on the "Find sweets" page and, if active,
    it can place orders through the partner portal.

    DESIGN:
    - Independent from public partner requests
    - Created through internal provisioning workflows
    - One-to-one with Django User for current MVP simplicity
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="store",
    )
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=500)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Store"
        verbose_name_plural = "Stores"

    def __str__(self) -> str:
        return self.name


class StaffAccount(models.Model):
    """
    Internal staff identity owned by the business domain.

    This model exists because Django's built-in flags are infrastructure-level
    concerns and are not expressive enough for the business distinction between:

    - restricted operational staff
    - full staff/admin

    IMPORTANT:
    - Restricted staff should use the staff portal, but not Django admin
    - Full staff may use both the staff portal and Django admin
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="staff_account",
    )
    access_level = models.CharField(
        max_length=20,
        choices=StaffAccessLevel.choices(),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["user__username"]
        verbose_name = "Staff account"
        verbose_name_plural = "Staff accounts"

    def __str__(self) -> str:
        return f"{self.user.username} ({self.access_level})"
