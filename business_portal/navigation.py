from __future__ import annotations

from dataclasses import dataclass

from django.urls import reverse
from django.utils.translation import gettext_lazy as _


@dataclass(frozen=True, slots=True)
class BusinessNavItem:
    """A primary navigation link for the business sales channel."""

    label: str
    route_name: str
    namespace: str
    icon: str = ""
    active_url_names: tuple[str, ...] = ()

    @property
    def href(self) -> str:
        return reverse(self.route_name)


BUSINESS_CATALOG_NAV_ITEM = BusinessNavItem(
    label=_("Catalog"),
    route_name="business_portal:catalog",
    namespace="business_portal",
    icon="lollipop",
    active_url_names=(
        "catalog",
        "catalog_product",
    ),
)

BUSINESS_FIND_SWEETS_NAV_ITEM = BusinessNavItem(
    label=_("Find Sweets"),
    route_name="public_site:find_sweets",
    namespace="public_site",
    icon="map-pin",
    active_url_names=("find_sweets",),
)

BUSINESS_FAQ_NAV_ITEM = BusinessNavItem(
    label=_("Q & A"),
    route_name="business_portal:faq",
    namespace="business_portal",
    icon="question",
    # Contact lives on the FAQ page.
    active_url_names=("faq", "contact"),
)


BUSINESS_ABOUT_NAV_ITEM = BusinessNavItem(
    label=_("About us"),
    route_name="public_site:about",
    namespace="public_site",
    icon="info",
    active_url_names=("about",),
)


BUSINESS_PRIMARY_NAV_ITEMS = (
    BUSINESS_CATALOG_NAV_ITEM,
    BUSINESS_FIND_SWEETS_NAV_ITEM,
    BUSINESS_FAQ_NAV_ITEM,
    BUSINESS_ABOUT_NAV_ITEM,
)


def build_business_primary_nav_items() -> tuple[BusinessNavItem, ...]:
    return BUSINESS_PRIMARY_NAV_ITEMS
