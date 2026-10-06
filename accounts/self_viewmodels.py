"""My account (/accounts/me/): the signed-in person's own account page,
in the same calm layout as an account on ops."""

from __future__ import annotations

from dataclasses import dataclass

from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from accounts.activity import AccountActivity
from accounts.activity_viewmodels import (
    AccountActivityRow,
    build_account_activity_rows,
)
from accounts.presentation import (
    AccountPresentation,
    build_account_presentation,
)
from accounts.roles import RoleSpec
from accounts.selectors import AccountRecord
from accounts.self_activity_links import self_activity_target_href
from common.page_tabs import PageTab

SELF_ACCOUNT_TABS = (
    PageTab(
        key="account",
        label="Account",
        icon="users",
        template="accounts/includes/self_tab_account.html",
    ),
    PageTab(
        key="activity",
        label="Activity",
        icon="inventory",
        template="accounts/includes/detail_tab_activity.html",
    ),
)


@dataclass(frozen=True, slots=True)
class AccountDetailContext:
    account: AccountPresentation
    activity_rows: tuple[AccountActivityRow, ...]
    back_url: str

    def as_dict(self) -> dict[str, object]:
        is_active = self.account.is_active

        return {
            "account": self.account,
            "activity_rows": self.activity_rows,
            "title": self.account.email,
            "status_key": "active" if is_active else "inactive",
            "status_label": self.account.status_label,
            "status_icon": "users" if is_active else "x",
            "activity_label": _activity_summary(len(self.activity_rows)),
            "password_change_href": reverse("password_change"),
            "page_tabs": SELF_ACCOUNT_TABS,
            "tabs_label": _("Account sections"),
            "back_url": self.back_url,
            "back_label": _("Back to start"),
        }


def build_self_account_detail_context(
    *,
    account: AccountRecord,
    activity_rows: tuple[AccountActivity, ...],
    back_url: str,
    role_spec: RoleSpec,
) -> AccountDetailContext:
    return AccountDetailContext(
        account=build_account_presentation(account),
        activity_rows=build_account_activity_rows(
            activity_rows,
            href_for=lambda activity: self_activity_target_href(
                activity=activity,
                role_spec=role_spec,
            ),
        ),
        back_url=back_url,
    )


def _activity_summary(activity_count: int) -> str:
    return ngettext(
        "%(count)d event",
        "%(count)d events",
        activity_count,
    ) % {
        "count": activity_count,
    }
