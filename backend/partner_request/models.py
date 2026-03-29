from django.db import models


class PartnerRequest(models.Model):
    """
    Incoming request from a store that wants to become a partner.

    This is reviewed manually and can later be converted into a Store.
    """

    name = models.CharField(max_length=200)
    store_name = models.CharField(max_length=200)

    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)

    address = models.TextField()

    message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    is_processed = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.store_name} ({self.name})"
