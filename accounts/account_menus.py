"""
Identity links for the shared navbar account slot.

No menu, only links, like the page links beside them: at the far right
"My account" (the account page, which has the logout: one rarely logs
out, so it needs no place in the navbar). Staff get one more link before
it, a switch between the public site and ops: "Ops dashboard" on the
public site, "Public site" in ops.

Logout is a POST action with CSRF protection; the account pages render
it (business_portal account tab, accounts self tab).
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
    account: AccountMenuItem
    switch: AccountMenuItem | None = None


MY_ACCOUNT_MENU_ITEM = AccountMenuItem(
    label=_("My account"),
    route_name="accounts:me",
    icon="users",
)

BUSINESS_ACCOUNT_MENU_ITEM = AccountMenuItem(
    label=_("My account"),
    route_name="business_portal:index",
    icon="users",
)

OPS_DASHBOARD_MENU_ITEM = AccountMenuItem(
    label=_("Ops dashboard"),
    route_name="ops_dashboard",
    icon="inventory",
)

PUBLIC_SITE_MENU_ITEM = AccountMenuItem(
    label=_("Public site"),
    route_name="storefront:product_list",
    icon="lollipop",
)


def build_storefront_account_menu(
    *,
    account_role: AccountRole,
    role_spec: RoleSpec,
) -> AccountMenu | None:
    """The account links while browsing the public storefront."""

    if role_spec.allows(Capability.VIEW_STAFF_OPS):
        return AccountMenu(
            account=MY_ACCOUNT_MENU_ITEM,
            switch=OPS_DASHBOARD_MENU_ITEM,
        )

    if account_role == AccountRole.BUSINESS_CUSTOMER:
        return build_business_account_menu()

    return None


def build_business_account_menu() -> AccountMenu:
    """The account link on the business customer site."""

    return AccountMenu(account=BUSINESS_ACCOUNT_MENU_ITEM)


def build_ops_account_menu() -> AccountMenu:
    """The account links inside the operations portal."""

    return AccountMenu(
        account=MY_ACCOUNT_MENU_ITEM,
        switch=PUBLIC_SITE_MENU_ITEM,
    )
