"""The password reset mail: plain text, and HTML in the shared mail frame
(logo, card, yellow button)."""

from __future__ import annotations

import pytest
from django.test import override_settings
from django.urls import reverse

from accounts.tests.factories import user_factory


@pytest.mark.django_db
@override_settings(
    LANGUAGE_CODE="en",
    SITE_URL="https://www.swedesweets.se",
)
def test_reset_mail_has_the_shared_html_frame(client, mailoutbox):
    user_factory(username="shop@example.com", email="shop@example.com")

    client.post(
        reverse("password_reset"),
        {"email": "shop@example.com"},
        HTTP_ACCEPT_LANGUAGE="en",
    )

    (mail,) = mailoutbox
    html, mimetype = mail.alternatives[0]

    assert mimetype == "text/html"
    assert "email-logo" in html
    assert "/accounts/reset/" in html
    assert "/accounts/reset/" in mail.body
