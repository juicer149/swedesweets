"""Customer footer stays quiet; signed-in account controls live on My account."""

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
def test_signed_in_account_controls_move_from_footer_to_profile(client):
    customer = customer_factory(name="Butiken i Chamonix")
    client.force_login(customer_user_factory(customer=customer))

    footer = _footer(client, "business_portal:faq")

    assert "Butiken i Chamonix" not in footer
    assert "Signed in as" not in footer
    assert f'action="{reverse("logout")}"' not in footer

    profile = client.get(reverse("business_portal:index")).content.decode()
    logout = profile.split('class="account-details__logout"', 1)[1].split(
        "</form>", 1
    )[0]
    assert f'method="post" action="{reverse("logout")}"' in logout
    assert "csrfmiddlewaretoken" in logout
