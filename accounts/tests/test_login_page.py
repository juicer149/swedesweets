from __future__ import annotations

import pytest
from django.test import override_settings
from django.urls import reverse

from accounts.forms import AccountPasswordChangeForm, LoginForm
from accounts.tests.factories import user_factory


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


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en")
def test_reset_page_uses_an_email_placeholder(client):
    response = client.get(reverse("password_reset"), HTTP_ACCEPT_LANGUAGE="en")

    assert response.status_code == 200
    html = response.content.decode()
    assert 'placeholder="Email"' in html
    assert 'class="form-label visually-hidden"' in html


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en")
def test_change_password_page_uses_the_field_labels_as_placeholders(client):
    client.force_login(user_factory())

    response = client.get(reverse("password_change"), HTTP_ACCEPT_LANGUAGE="en")

    assert response.status_code == 200
    assert isinstance(response.context["form"], AccountPasswordChangeForm)
    html = response.content.decode()
    assert 'placeholder="Old password"' in html
    assert 'placeholder="New password"' in html
    assert 'placeholder="New password confirmation"' in html
