"""Only customer catalog/reading pages participate in persistent navigation."""

import pytest
from django.urls import reverse

from accounts.tests.factories import customer_user_factory, full_staff_user_factory
from customers.tests.factories import customer_factory


@pytest.mark.django_db
@pytest.mark.parametrize(
    "route,page",
    [
        ("storefront:product_list", "catalog"),
        ("public_site:find_sweets", "find-sweets"),
        ("public_site:faq", "faq"),
        ("public_site:about", "about"),
    ],
)
def test_public_navigation_pages_keep_native_links_and_page_identity(
    client, route, page
):
    response = client.get(reverse(route))
    assert response.status_code == 200
    html = response.content.decode()
    assert f'data-public-page="{page}"' in html
    assert "js/public-navigation." in html
    for destination in [
        "storefront:product_list",
        "public_site:faq",
        "public_site:about",
    ]:
        assert f'href="{reverse(destination)}"' in html
    if page in {"catalog", "faq"}:
        assert "<script data-public-page-script" in html


@pytest.mark.django_db
def test_business_catalog_uses_the_same_navigation_surface(client):
    client.force_login(customer_user_factory(customer=customer_factory()))
    for route, page in [
        ("business_portal:catalog", "catalog"),
        ("business_portal:faq", "faq"),
    ]:
        html = client.get(reverse(route)).content.decode()
        assert f'data-public-page="{page}"' in html
        assert "js/public-navigation." in html
        assert "<script data-public-page-script" in html
        assert f'href="{reverse("business_portal:faq")}"' in html


@pytest.mark.django_db
def test_ops_does_not_load_public_navigation(client):
    client.force_login(full_staff_user_factory())
    response = client.get(reverse("ops_dashboard"))
    assert response.status_code == 200
    html = response.content.decode()
    assert "js/public-navigation." not in html
    assert "data-public-page=" not in html


@pytest.mark.django_db
def test_checkout_keeps_its_own_flow_surface(client):
    html = client.get(reverse("storefront:cart")).content.decode()
    assert "data-order-flow-page" in html
    assert "data-public-page=" not in html
