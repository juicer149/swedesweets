from __future__ import annotations

from dataclasses import dataclass

from django.urls import reverse

from accounts.selectors import AccountRecord
from common.page_header import PageHeader, PageHeaderAction
from ops_portal.accounts.presentation import (
    account_status_icon,
    build_ops_account_presentation,
)

ACCOUNT_VIEW_INTERNAL = "internal"
ACCOUNT_VIEW_CUSTOMER = "customer"
ACCOUNT_VIEW_UNLINKED = "unlinked"


@dataclass(frozen=True, slots=True)
class AccountViewLink:
    key: str
    label: str
    href: str
    is_active: bool


@dataclass(frozen=True, slots=True)
class AccountPageRow:
    user_id: int
    email: str
    role_label: str
    linked_identity: str
    linked_identity_href: str
    status_label: str
    status_tone: str
    is_active: bool
    detail_href: str
    icon: str

    @property
    def meta(self) -> str:
        """Phones: the grey line under the email: the role, and the
        customer for a customer login (staff identities only repeat the
        role)."""

        if self.linked_identity_href:
            return f"{self.role_label} · {self.linked_identity}"

        return self.role_label


def build_accounts_page_header(*, active_view: str) -> PageHeader:
    return PageHeader(
        title="Accounts",
        title_id="accounts-title",
        description="",
        action=_build_accounts_page_action(active_view=active_view),
    )


def build_account_view_links(
    *,
    active_view: str,
) -> tuple[AccountViewLink, ...]:
    return (
        AccountViewLink(
            key=ACCOUNT_VIEW_INTERNAL,
            label="Internal",
            href=_accounts_view_href(ACCOUNT_VIEW_INTERNAL),
            is_active=active_view == ACCOUNT_VIEW_INTERNAL,
        ),
        AccountViewLink(
            key=ACCOUNT_VIEW_CUSTOMER,
            label="Customer",
            href=_accounts_view_href(ACCOUNT_VIEW_CUSTOMER),
            is_active=active_view == ACCOUNT_VIEW_CUSTOMER,
        ),
        AccountViewLink(
            key=ACCOUNT_VIEW_UNLINKED,
            label="Unlinked",
            href=_accounts_view_href(ACCOUNT_VIEW_UNLINKED),
            is_active=active_view == ACCOUNT_VIEW_UNLINKED,
        ),
    )


def build_account_page_rows(
    records: tuple[AccountRecord, ...],
) -> tuple[AccountPageRow, ...]:
    return tuple(
        _build_account_page_row(record)
        for record in records
    )


def _build_account_page_row(
    record: AccountRecord,
) -> AccountPageRow:
    account = build_ops_account_presentation(record)
    detail_href = reverse(
        "ops_accounts:detail",
        kwargs={"user_id": account.user_id},
    )

    return AccountPageRow(
        user_id=account.user_id,
        email=account.email,
        role_label=account.role_label,
        linked_identity=account.linked_identity,
        linked_identity_href=account.linked_identity_href,
        status_label=account.status_label,
        status_tone=_status_tone(is_active=account.is_active),
        is_active=account.is_active,
        detail_href=detail_href,
        icon=account_status_icon(account),
    )


def _build_accounts_page_action(
    *,
    active_view: str,
) -> PageHeaderAction | None:
    if active_view == ACCOUNT_VIEW_INTERNAL:
        return PageHeaderAction(
            label="Add account",
            href=reverse("ops_accounts:create_internal"),
            icon="plus",
            aria_label="Create internal staff account",
        )

    if active_view == ACCOUNT_VIEW_CUSTOMER:
        # A shop's login comes with an invitation (Customers).
        return PageHeaderAction(
            label="Invite shop",
            href=reverse("ops_customers:invite"),
            icon="mail",
            aria_label="Invite a new shop to order online",
        )

    return None


def _accounts_view_href(view: str) -> str:
    return f"{reverse('ops_accounts:index')}?view={view}#accounts-list"


def _status_tone(*, is_active: bool) -> str:
    """Row tone: active rows in green; inactive rows have no surface."""

    if is_active:
        return "success"

    return "inactive"
