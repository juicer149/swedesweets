"""
Staff settings switch between public and ops; the account dropdown and
ops footer both provide the personal profile and a protected logout.
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
    # The ops footer stays available independently of the account dropdown.
    assert "site-footer" not in html
    assert footer.count(f'action="{reverse("logout")}"') == 1


@pytest.mark.django_db
def test_staff_settings_switch_to_public_and_account_menu_links_to_profile(client):
    client.force_login(full_staff_user_factory())

    html = client.get(reverse("ops_dashboard")).content.decode()

    navbar = html.split("<header", 1)[1].split("</header>", 1)[0]
    assert 'class="theme-switch site-switch"' in navbar
    assert 'method="get"' in navbar
    assert f'action="{reverse("storefront:product_list")}"' in navbar
    assert 'class="account-menu__panel"' in navbar
    assert f'href="{reverse("accounts:me")}"' in navbar
