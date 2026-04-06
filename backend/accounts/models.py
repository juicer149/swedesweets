from django.conf import settings
from django.db import models


class Store(models.Model):
    """
    Internal, trusted representation of a retail customer.

    A Store is the business entity that participates in the system:
    it can be shown publicly on the "Find sweets" page and, if active,
    it can place orders through the partner portal.

    DESIGN:
    - Independent from public partner requests
    - Created manually by admin for the current MVP
    - One-to-one with Django User for MVP simplicity

    WHY THE 1:1 RELATION:
    The current business setup is small: each store effectively has one
    responsible manager using one login for ordering. Because of that,
    a one-user-per-store model keeps the system simple and explicit.

    INVARIANTS:
    - A Store must always be linked to a Django User
    - Only active stores should use the ordering portal
    - A store may be active internally without necessarily being shown
      publicly forever; public listing rules currently live in read selectors
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
