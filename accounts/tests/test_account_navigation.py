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
    return response.content.decode().split(
        'class="account-menu__panel mobile-menu-panel"', 1
    )[1].split("</details>", 1)[0]


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
    assert 'class="site-preferences__site"' not in response.content.decode()
    assert "site-preferences__logout" not in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory", [full_staff_user_factory, restricted_staff_user_factory]
)
def test_staff_site_link_and_account_destinations_follow_navigation_context(
    client, factory
):
    client.force_login(factory())
    for route, target in [
        ("storefront:product_list", "ops_dashboard"),
        ("ops_dashboard", "storefront:product_list"),
        ("accounts:me", "storefront:product_list"),
    ]:
        response = client.get(reverse(route))
        assert response.status_code == 200
        menu = response.context["account_menu"]
        panel = _account_panel(response)
        assert menu.account.href == reverse("accounts:me")
        assert menu.orders is None
        assert menu.switch.href == reverse(target)
        assert f'href="{reverse("accounts:me")}"' in panel
        assert reverse("business_portal:orders") not in panel
        content = response.content.decode()
        site_link = content.split('class="site-preferences__site">', 1)[1].split(
            "</div>", 1
        )[0]
        assert f'href="{reverse(target)}"' in site_link
        assert 'role="switch"' not in site_link
        assert "site-preferences__logout" not in content


@pytest.mark.django_db
def test_anonymous_account_dropdown_has_only_login_and_no_site_link(client):
    content = client.get(reverse("storefront:product_list")).content.decode()
    assert 'class="account-menu"' in content
    panel = content.split('class="account-menu__panel mobile-menu-panel"', 1)[1].split(
        "</details>", 1
    )[0]
    assert f'href="{reverse("login")}"' in panel
    assert 'account-menu__logout' not in panel
    assert reverse("business_portal:orders") not in panel
    assert 'class="site-preferences__site"' not in content


@pytest.mark.django_db
@pytest.mark.parametrize("route,account_current,cart_current", [
    ("business_portal:index", True, False),
    ("business_portal:orders", True, False),
    ("business_portal:catalog", False, False),
    ("business_portal:cart", False, True),
])
def test_business_header_marks_the_current_destination(
    client, route, account_current, cart_current
):
    client.force_login(customer_user_factory(customer=customer_factory()))
    response = client.get(reverse(route), follow=True)
    assert response.status_code == 200
    html = response.content.decode()
    account = html.split('class="account-menu__trigger', 1)[1].split("</summary>", 1)[0]
    cart = html.split('class="site-nav-cart__trigger', 1)[1].split("</summary>", 1)[0]
    assert ('aria-current="page"' in account) is account_current
    assert ('aria-current="page"' in cart) is cart_current


@pytest.mark.django_db
def test_retail_cart_marks_its_header_icon_current(client):
    response = client.get(reverse("storefront:cart"))
    assert response.status_code == 200
    cart = response.content.decode().split('class="site-nav-cart__trigger', 1)[1].split(
        "</summary>", 1
    )[0]
    assert 'aria-current="page"' in cart
