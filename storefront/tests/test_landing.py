from __future__ import annotations

from decimal import Decimal

import pytest
from django.http import HttpResponse
from django.urls import reverse

from accounts.tests.factories import (
    customer_membership_factory,
    user_factory,
)
from carts.services import create_cart
from common.channels import SalesChannel
from customers.tests.factories import customer_factory
from retail.services import add_retail_cart_line
from retail.tests.factories import retail_product_price_factory
from storefront.cart import COOKIE_NAME, COOKIE_SALT
from storefront.navigation import PUBLIC_PRIMARY_NAV_ITEMS


def _landing_html(client) -> str:
    response = client.get(reverse("index"), HTTP_ACCEPT_LANGUAGE="en")

    assert response.status_code == 200
    return response.content.decode()


@pytest.mark.django_db
def test_landing_uses_original_stacked_logo_at_all_viewport_sizes(client):
    html = _landing_html(client)

    assert 'class="brand-logo landing__logo-art"' in html
    assert html.count('class="brand-logo__wordmark"') == 1
    assert html.count('class="brand-logo__crown"') == 1
    assert 'brand-logo--wide' not in html
    assert "swedesweets-logo-wide.svg" not in html


@pytest.mark.django_db
def test_navbar_and_login_use_the_traced_logo(client):
    faq = client.get(reverse("public_site:faq")).content.decode()
    login = client.get(reverse("login")).content.decode()

    assert 'class="brand-logo site-brand__logo"' in faq
    assert 'class="brand-logo entrance-header__logo"' in login
    assert 'class="brand-logo__wordmark"' in faq
    assert 'class="brand-logo__wordmark"' in login


@pytest.mark.django_db
def test_start_page_is_a_menu_of_the_navbar_links(client):
    html = _landing_html(client)

    menu = html[html.index("data-landing-menu"):]
    for item in PUBLIC_PRIMARY_NAV_ITEMS:
        assert f'href="{item.href}"' in menu
    # The crown starts on the first one.
    assert menu.count("landing-menu__link--chosen") == 1
    assert "Sweden’s sweetest tradition" in html


@pytest.mark.django_db
def test_start_page_has_no_navbar_or_footer_but_a_login(client):
    html = _landing_html(client)

    assert "site-header" not in html
    assert "site-footer" not in html
    assert f'class="landing__account" href="{reverse("login")}"' in html


@pytest.mark.django_db
def test_start_page_shows_the_cart_only_once_it_holds_something(client):
    assert "landing__cart" not in _landing_html(client)

    cart = create_cart(channel=SalesChannel.RETAIL)
    price = retail_product_price_factory(enabled=True, price=Decimal("10.00"))
    add_retail_cart_line(cart=cart, commercial_price_id=price.id, quantity=2)

    response = HttpResponse()
    response.set_signed_cookie(COOKIE_NAME, str(cart.id), salt=COOKIE_SALT)
    client.cookies[COOKIE_NAME] = response.cookies[COOKIE_NAME].value

    html = _landing_html(client)
    assert 'class="landing__cart"' in html
    assert 'class="landing__cart-mobile"' in html
    assert 'data-mobile-menu="cart"' in html
    assert 'data-retail-cart="true"' in html
    assert 'data-cart-panel-scroll' in html
    assert 'js/navbar-cart.' in html
    assert f'href="{reverse("storefront:cart")}"' in html


@pytest.mark.django_db
def test_business_customer_gets_their_menu_and_account(client):
    user = user_factory(username="customer@example.com")
    customer_membership_factory(user=user, customer=customer_factory())
    client.force_login(user)

    html = _landing_html(client)

    menu = html[html.index("data-landing-menu"):]
    assert f'href="{reverse("business_portal:catalog")}"' in menu
    assert 'class="account-menu__trigger' in html
    assert f'href="{reverse("business_portal:index")}"' in html
    bottom = html.split('class="landing__bottom">', 1)[1]
    assert f'method="post" action="{reverse("logout")}"' in bottom
    assert "csrfmiddlewaretoken" in bottom
    assert "My account" not in bottom
    assert f'href="{reverse("login")}"' not in html
