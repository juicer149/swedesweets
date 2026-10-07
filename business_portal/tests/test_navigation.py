from django.urls import reverse

from business_portal.navigation import (
    build_business_primary_nav_items,
)


def test_business_navigation_has_shared_site_shape():
    items = build_business_primary_nav_items()

    assert tuple(
        item.label
        for item in items
    ) == (
        "Catalog",
        "Find Sweets",
        "FAQ",
        "About us",
    )


def test_business_catalog_uses_business_sales_channel():
    items = build_business_primary_nav_items()

    catalog_item = items[0]

    assert (
        catalog_item.route_name
        == "business_portal:catalog"
    )
    assert (
        catalog_item.href
        == reverse("business_portal:catalog")
    )


def test_business_find_sweets_is_public_and_faq_stays_in_business_portal():
    items = build_business_primary_nav_items()

    find_sweets_item = items[1]
    faq_item = items[2]

    assert find_sweets_item.href == reverse("public_site:find_sweets")
    assert find_sweets_item.icon == "map-pin"

    assert (
        faq_item.route_name
        == "business_portal:faq"
    )
    assert (
        faq_item.href
        == reverse("business_portal:faq")
    )
    assert faq_item.icon == "question"


def test_about_is_the_shared_public_page():
    about_item = build_business_primary_nav_items()[3]

    assert about_item.href == reverse("public_site:about")
    assert about_item.icon == "info"
