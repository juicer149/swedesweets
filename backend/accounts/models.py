from django.conf import settings
from django.db import models


class Store(models.Model):
    """
    Internal, trusted representation of a retail customer.

    A Store exists inside the system and is allowed to act in it,
    for example by placing orders.

    DESIGN:
    - Independent from PartnerRequest
    - Can be created via PartnerRequest approval or manually by admin
    - One-to-one with Django User for MVP simplicity

    INVARIANTS:
    - A Store must always be linked to a User
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

    def __str__(self) -> str:
        return self.name
