from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.urls import reverse

from accounts.models import StaffAccount
from ops_portal.accounts.forms import (
    CustomerAccountCreateForm,
    InternalAccountCreateForm,
    InternalAccountEditForm,
)
from ops_portal.accounts.list_viewmodels import (
    ACCOUNT_VIEW_CUSTOMER,
    ACCOUNT_VIEW_INTERNAL,
)


@dataclass(frozen=True, slots=True)
class AccountFormContext:
    title: str
    submit_label: str
    cancel_url: str
    form: (
        CustomerAccountCreateForm
        | InternalAccountCreateForm
        | InternalAccountEditForm
    )
    staff_account: StaffAccount | None = None

    def as_dict(self) -> dict[str, Any]:
        context: dict[str, Any] = {
            "title": self.title,
            "submit_label": self.submit_label,
            "cancel_url": self.cancel_url,
            "form": self.form,
            "staff_account": self.staff_account,
        }

        if self.staff_account is not None:
            is_active = self.staff_account.user.is_active
            context |= {
                "status_key": "active" if is_active else "inactive",
                "status_label": "Active" if is_active else "Inactive",
                "status_icon": "users" if is_active else "x",
                "access_level_label": (
                    self.staff_account.get_access_level_display()
                ),
            }

        return context


def build_create_customer_account_form_context(
    *,
    form: CustomerAccountCreateForm,
) -> AccountFormContext:
    return AccountFormContext(
        form=form,
        title="Create customer account",
        submit_label="Create account",
        cancel_url=_accounts_customer_url(),
    )


def build_create_internal_account_form_context(
    *,
    form: InternalAccountCreateForm,
) -> AccountFormContext:
    return AccountFormContext(
        form=form,
        title="Create internal account",
        submit_label="Create account",
        cancel_url=_accounts_internal_url(),
    )


def build_edit_internal_account_form_context(
    *,
    form: InternalAccountEditForm,
    staff_account: StaffAccount,
) -> AccountFormContext:
    return AccountFormContext(
        form=form,
        staff_account=staff_account,
        title=f"Edit {staff_account.user.email}",
        submit_label="Save account",
        cancel_url=reverse(
            "ops_accounts:detail",
            kwargs={
                "user_id": staff_account.user_id,
            },
        ),
    )


def _accounts_customer_url() -> str:
    return (
        f"{reverse('ops_accounts:index')}"
        f"?view={ACCOUNT_VIEW_CUSTOMER}#accounts-list"
    )


def _accounts_internal_url() -> str:
    return (
        f"{reverse('ops_accounts:index')}"
        f"?view={ACCOUNT_VIEW_INTERNAL}#accounts-list"
    )
