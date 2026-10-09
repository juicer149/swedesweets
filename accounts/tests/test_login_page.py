from __future__ import annotations

import pytest
from django.test import override_settings
from django.urls import reverse

from accounts.forms import AccountPasswordChangeForm, LoginForm, split_password_rules
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


@pytest.mark.django_db
def test_the_ways_in_are_blue_and_the_shop_is_not(client):
    for name in ("login", "password_reset", "password_reset_done"):
        html = client.get(reverse(name)).content.decode()
        assert '<body class="on-blue">' in html, name
        assert "swedesweets-logo-cream" in html, name

    client.force_login(user_factory())
    html = client.get(reverse("password_change")).content.decode()
    assert "on-blue" not in html


@pytest.mark.django_db
def test_login_shows_the_burst_while_it_logs_in(client):
    html = client.get(reverse("login")).content.decode()

    assert "data-login" in html
    assert 'data-status-burst="default"' in html
    assert "js/status_burst" in html
    assert "js/login" in html


def test_password_rules_lead_is_split_off():
    lead, items = split_password_rules([
        "Your password must contain at least 8 characters.",
        "Your password can’t be entirely numeric.",
    ])
    assert lead == "Your password"
    assert items == [
        "must contain at least 8 characters.",
        "can’t be entirely numeric.",
    ]


def test_password_rules_without_a_common_lead_stay_whole():
    assert split_password_rules(["Short.", "Different."]) == (
        "",
        ["Short.", "Different."],
    )
    assert split_password_rules(["Only one rule."]) == ("", ["Only one rule."])


def test_password_rules_work_in_french():
    lead, items = split_password_rules([
        "Votre mot de passe doit contenir au minimum 8 caractères.",
        "Votre mot de passe ne peut pas être entièrement numérique.",
    ])
    assert lead == "Votre mot de passe"
    assert items[0].startswith("doit contenir")


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en")
def test_reset_link_page_looks_like_changing_the_password(client):
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.encoding import force_bytes
    from django.utils.http import urlsafe_base64_encode

    from accounts.forms import AccountSetPasswordForm

    user = user_factory()
    url = reverse(
        "password_reset_confirm",
        kwargs={
            "uidb64": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": default_token_generator.make_token(user),
        },
    )

    response = client.get(url, follow=True, HTTP_ACCEPT_LANGUAGE="en")

    assert response.status_code == 200
    assert isinstance(response.context["form"], AccountSetPasswordForm)

    html = response.content.decode()
    # No heading; the rules as a dropdown above the fields, placeholders.
    assert "<h1" not in html
    assert "page__rules" in html
    assert 'placeholder="New password"' in html
    assert 'class="form-label visually-hidden"' in html
