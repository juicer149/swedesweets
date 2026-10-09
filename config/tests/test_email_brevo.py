"""Brevo (anymail) is wired in: the backend loads with the settings'
key, and a set EMAIL_REPLY_TO goes on every mail it sends."""

from __future__ import annotations

from django.core.mail import get_connection
from django.test import override_settings

BREVO_BACKEND = "anymail.backends.brevo.EmailBackend"


@override_settings(
    ANYMAIL={
        "BREVO_API_KEY": "test-key",
        "SEND_DEFAULTS": {"reply_to": ["info@swedesweets.se"]},
    }
)
def test_brevo_backend_loads_with_key_and_reply_to():
    connection = get_connection(BREVO_BACKEND)

    assert connection.api_key == "test-key"
    assert connection.send_defaults == {"reply_to": ["info@swedesweets.se"]}
