"""
The navbar's account slot and the ops footer: staff switch between the
public site and ops in the navbar, and find their own account and the
logout in the ops footer.
"""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.tests.factories import (
    full_staff_user_factory,
    restricted_staff_user_factory,
)


def _footer(html: str) -> str:
    return html[html.index('class="ops-footer"'):]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "make_user",
    [full_staff_user_factory, restricted_staff_user_factory],
)
def test_ops_footer_has_my_account_and_logout_for_all_staff(client, make_user):
    client.force_login(make_user())

    html = client.get(reverse("ops_dashboard")).content.decode()

    footer = _footer(html)
    assert f'href="{reverse("accounts:me")}"' in footer
    assert f'action="{reverse("logout")}"' in footer
    # Not the customers' footer, and no logout up in the navbar.
    assert "site-footer" not in html
    assert html.count(f'action="{reverse("logout")}"') == 1


@pytest.mark.django_db
def test_staff_navbar_switches_to_the_public_site_in_ops(client):
    client.force_login(full_staff_user_factory())

    html = client.get(reverse("ops_dashboard")).content.decode()

    navbar = html[: html.index('class="ops-footer"')]
    assert f'href="{reverse("storefront:product_list")}"' in navbar
    assert f'href="{reverse("accounts:me")}"' not in navbar
