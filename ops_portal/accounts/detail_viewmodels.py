from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from accounts.activity import AccountActivity
from accounts.activity_viewmodels import AccountActivityRow
from accounts.presentation import AccountPresentation
from accounts.roles import RoleSpec
from accounts.selectors import AccountRecord
from common.page_tabs import PageTab
from ops_portal.accounts.access import (
    can_manage_customer_account_status,
)
from ops_portal.accounts.activity_viewmodels import (
    build_ops_account_activity_rows,
)
from ops_portal.accounts.presentation import (
    account_status_icon,
    account_status_key,
    build_ops_account_presentation,
)

ACCOUNT_DETAIL_TABS = (
    PageTab(
        key="account",
        label="Account",
        icon="users",
        template="ops_portal/accounts/includes/detail_tab_account.html",
    ),
    PageTab(
        key="activity",
        label="Activity",
        icon="inventory",
        template="accounts/includes/detail_tab_activity.html",
    ),
)


@dataclass(frozen=True, slots=True)
class AccountStatusAction:
    """Activate or deactivate a customer login (a page that confirms)."""

    label: str
    href: str
    is_danger: bool


@dataclass(frozen=True, slots=True)
class AccountDetailContext:
    account: AccountPresentation
    activity_rows: tuple[AccountActivityRow, ...]
    edit_href: str
    status_action: AccountStatusAction | None
    back_url: str

    def as_dict(self) -> dict[str, object]:
        return {
            "account": self.account,
            "activity_rows": self.activity_rows,
            "edit_href": self.edit_href,
            "status_action": self.status_action,
            "title": self.account.email,
            "status_key": account_status_key(self.account),
            "status_label": self.account.status_label,
            "status_icon": account_status_icon(self.account),
            "activity_label": _activity_summary(len(self.activity_rows)),
            "page_tabs": ACCOUNT_DETAIL_TABS,
            "tabs_label": _("Account sections"),
            "back_url": self.back_url,
            "back_label": _("Back to accounts"),
        }


@dataclass(frozen=True, slots=True)
class CustomerAccountStatusContext:
    title: str
    note: str
    submit_label: str
    is_danger: bool
    cancel_url: str
    account_user: Any
    customer: Any

    def as_dict(self) -> dict[str, object]:
        is_active = self.account_user.is_active

        return {
            "title": self.title,
            "note": self.note,
            "submit_label": self.submit_label,
            "is_danger": self.is_danger,
            "cancel_url": self.cancel_url,
            "account_user": self.account_user,
            "customer": self.customer,
            "status_key": "active" if is_active else "inactive",
            "status_label": _active_status_label(is_active=is_active),
            "status_icon": "users" if is_active else "x",
        }


def build_account_detail_context(
    *,
    account: AccountRecord,
    activity_rows: tuple[AccountActivity, ...],
    back_url: str,
    role_spec: RoleSpec,
    edit_url: str = "",
) -> AccountDetailContext:
    presented_account = build_ops_account_presentation(account)

    return AccountDetailContext(
        account=presented_account,
        activity_rows=build_ops_account_activity_rows(activity_rows),
        edit_href=edit_url,
        status_action=_build_status_action(
            account=presented_account,
            role_spec=role_spec,
        ),
        back_url=back_url,
    )


def build_customer_account_status_context(
    *,
    membership: Any,
    is_active: bool,
) -> CustomerAccountStatusContext:
    account_user = membership.user

    return CustomerAccountStatusContext(
        title=account_user.email,
        note=_customer_account_status_note(is_active=is_active),
        submit_label=_customer_account_status_action_label(
            is_active=is_active,
        ),
        is_danger=not is_active,
        cancel_url=reverse(
            "ops_accounts:detail",
            kwargs={
                "user_id": account_user.pk,
            },
        ),
        account_user=account_user,
        customer=membership.customer,
    )


def customer_account_status_success_message(
    *,
    email: str,
    is_active: bool,
) -> str:
    if is_active:
        return _("Customer account %(email)s activated.") % {
            "email": email,
        }

    return _("Customer account %(email)s deactivated.") % {
        "email": email,
    }


def _build_status_action(
    *,
    account: AccountPresentation,
    role_spec: RoleSpec,
) -> AccountStatusAction | None:
    if not can_manage_customer_account_status(
        target_account_role=account.account_role,
        role_spec=role_spec,
    ):
        return None

    if account.is_active:
        return AccountStatusAction(
            label=_("Deactivate login"),
            href=reverse(
                "ops_accounts:deactivate_customer_account",
                kwargs={"user_id": account.user_id},
            ),
            is_danger=True,
        )

    return AccountStatusAction(
        label=_("Activate login"),
        href=reverse(
            "ops_accounts:activate_customer_account",
            kwargs={"user_id": account.user_id},
        ),
        is_danger=False,
    )


def _activity_summary(
    activity_count: int,
) -> str:
    return ngettext(
        "%(count)d event",
        "%(count)d events",
        activity_count,
    ) % {
        "count": activity_count,
    }


def _customer_account_status_action_label(
    *,
    is_active: bool,
) -> str:
    if is_active:
        return _("Activate login")

    return _("Deactivate login")


def _customer_account_status_note(
    *,
    is_active: bool,
) -> str:
    if is_active:
        return _("Allow this customer account to log in again.")

    return _(
        "Prevent this customer account from logging in. "
        "Existing customer data and historical records are kept."
    )


def _active_status_label(
    *,
    is_active: bool,
) -> str:
    if is_active:
        return _("Active")

    return _("Inactive")
