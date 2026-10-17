from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.tests.factories import (
    customer_user_factory,
    full_staff_user_factory,
    restricted_staff_user_factory,
)
from customers.tests.factories import customer_factory


def _account_panel(response):
    return response.content.decode().split('class="account-menu__panel">', 1)[1].split(
        "</details>", 1
    )[0]


@pytest.mark.django_db
def test_business_account_dropdown_has_profile_orders_and_post_logout(client):
    client.force_login(customer_user_factory(customer=customer_factory()))
    response = client.get(reverse("business_portal:index"))
    menu = response.context["account_menu"]
    panel = _account_panel(response)

    assert menu.account.href == reverse("business_portal:index")
    assert menu.orders.href == reverse("business_portal:orders")
    assert menu.switch is None
    assert f'href="{menu.account.href}"' in panel
    assert f'href="{menu.orders.href}"' in panel
    assert f'method="post" action="{reverse("logout")}"' in panel
    assert 'name="csrfmiddlewaretoken"' in panel
    assert 'class="theme-switch site-switch"' not in response.content.decode()
    assert "site-preferences__logout" not in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory", [full_staff_user_factory, restricted_staff_user_factory]
)
def test_staff_site_switch_and_account_destinations_follow_navigation_context(
    client, factory
):
    client.force_login(factory())
    for route, is_ops, target in [
        ("storefront:product_list", False, "ops_dashboard"),
        ("ops_dashboard", True, "storefront:product_list"),
        ("accounts:me", True, "storefront:product_list"),
    ]:
        response = client.get(reverse(route))
        assert response.status_code == 200
        menu = response.context["account_menu"]
        panel = _account_panel(response)
        assert menu.account.href == reverse("accounts:me")
        assert menu.orders is None
        assert menu.site_is_ops is is_ops
        assert menu.switch.href == reverse(target)
        assert f'href="{reverse("accounts:me")}"' in panel
        assert reverse("business_portal:orders") not in panel
        content = response.content.decode()
        site_switch = content.split('class="theme-switch site-switch"', 1)[1].split(
            "</button>", 1
        )[0]
        assert f'aria-checked="{str(is_ops).lower()}"' in site_switch
        assert f'action="{reverse(target)}"' in content
        assert "site-preferences__logout" not in content


@pytest.mark.django_db
def test_anonymous_header_has_no_account_dropdown_or_site_switch(client):
    content = client.get(reverse("storefront:product_list")).content.decode()
    assert 'class="account-menu"' not in content
    assert 'class="theme-switch site-switch"' not in content
