"""Navbar account links and staff-only site switching.

Builders choose destinations; shared templates render the account disclosure
and the settings site link. Logout stays a CSRF-protected POST action.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from accounts.roles import AccountRole, Capability, RoleSpec


@dataclass(frozen=True, slots=True)
class AccountMenuItem:
    label: str
    route_name: str
    icon: str = ""

    @property
    def href(self) -> str:
        return reverse(self.route_name)


@dataclass(frozen=True, slots=True)
class AccountMenu:
    account: AccountMenuItem | None = None
    switch: AccountMenuItem | None = None
    orders: AccountMenuItem | None = None


BUSINESS_ACCOUNT_MENU_ITEM = AccountMenuItem(
    label=_("My account"),
    route_name="business_portal:index",
    icon="user",
)

STAFF_ACCOUNT_MENU_ITEM = AccountMenuItem(
    label=_("My account"),
    route_name="accounts:me",
    icon="user",
)

BUSINESS_ORDERS_MENU_ITEM = AccountMenuItem(
    label=_("Order history"),
    route_name="business_portal:orders",
)

OPS_DASHBOARD_MENU_ITEM = AccountMenuItem(
    label=_("Ops dashboard"),
    route_name="ops_dashboard",
    icon="wrench",
)

PUBLIC_SITE_MENU_ITEM = AccountMenuItem(
    label=_("Public site"),
    route_name="storefront:product_list",
    icon="storefront",
)


def build_storefront_account_menu(
    *,
    account_role: AccountRole,
    role_spec: RoleSpec,
) -> AccountMenu | None:
    """Account destinations and optional staff site switch on the storefront."""

    if role_spec.allows(Capability.VIEW_STAFF_OPS):
        return AccountMenu(
            account=STAFF_ACCOUNT_MENU_ITEM,
            switch=OPS_DASHBOARD_MENU_ITEM,
        )

    if account_role == AccountRole.BUSINESS_CUSTOMER:
        return build_business_account_menu()

    return None


def build_business_account_menu() -> AccountMenu:
    """The account link on the business customer site."""

    return AccountMenu(
        account=BUSINESS_ACCOUNT_MENU_ITEM,
        orders=BUSINESS_ORDERS_MENU_ITEM,
    )


def build_ops_account_menu() -> AccountMenu:
    """The account links inside the operations portal."""

    return AccountMenu(
        account=STAFF_ACCOUNT_MENU_ITEM,
        switch=PUBLIC_SITE_MENU_ITEM,
    )
