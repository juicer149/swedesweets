from __future__ import annotations

import pytest
from django.test import override_settings
from django.urls import reverse

from accounts.forms import LoginForm


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en")
def test_login_page_uses_placeholders_and_keeps_labels_for_screen_readers(client):
    response = client.get(reverse("login"), HTTP_ACCEPT_LANGUAGE="en")

    assert response.status_code == 200
    assert isinstance(response.context["form"], LoginForm)

    html = response.content.decode()
    assert 'placeholder="Username"' in html
    assert 'placeholder="Password"' in html
    assert 'class="form-label visually-hidden"' in html
