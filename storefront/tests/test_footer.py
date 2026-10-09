"""The footer under the icons: a login for shops, or who is signed in
and Log out."""

from __future__ import annotations

import pytest
from django.test import override_settings
from django.urls import reverse

from accounts.tests.factories import user_factory


def _footer(client) -> str:
    html = client.get(reverse("public_site:about")).content.decode()
    return html[html.index('class="site-footer"'):]


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en")
def test_visitors_get_a_reseller_login(client):
    footer = _footer(client)

    assert f'href="{reverse("login")}"' in footer
    assert f'action="{reverse("logout")}"' not in footer


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en")
def test_signed_in_users_see_who_they_are_and_can_log_out(client):
    client.force_login(user_factory(username="shop@example.com"))

    footer = _footer(client)

    assert "shop@example.com" in footer
    assert f'action="{reverse("logout")}"' in footer
