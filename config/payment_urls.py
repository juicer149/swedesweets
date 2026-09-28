from __future__ import annotations

from django.urls import path

from retail import payment_webhooks


app_name = "payments"


urlpatterns = [
    path(
        "sumup/webhook/",
        payment_webhooks.sumup_webhook,
        name="sumup_webhook",
    ),
]
