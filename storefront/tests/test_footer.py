"""The footer under the icons: a login for shops, or who is signed in
and Log out."""

from __future__ import annotations

import pytest
from django.test import override_settings
from django.urls import reverse

from accounts.tests.factories import customer_user_factory
from customers.tests.factories import customer_factory


def _footer(client, url_name: str = "public_site:about") -> str:
    html = client.get(reverse(url_name)).content.decode()
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
    customer = customer_factory(name="Butiken i Chamonix")
    client.force_login(customer_user_factory(customer=customer))

    footer = _footer(client, "business_portal:faq")

    assert "Butiken i Chamonix" in footer
    assert f'action="{reverse("logout")}"' in footer
