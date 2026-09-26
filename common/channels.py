from django.db import models


class SalesChannel(models.TextChoices):
    RETAIL = "retail", "Retail"
    BUSINESS = "business", "Business"
