from __future__ import annotations

from django.urls import path

from payments import fake_views
from retail import payment_webhooks

app_name = "payments"


urlpatterns = [
    path(
        "sumup/webhook/",
        payment_webhooks.sumup_webhook,
        name="sumup_webhook",
    ),
    path(
        "fake/<str:payment_id>/",
        fake_views.fake_checkout,
        name="fake_checkout",
    ),
]
