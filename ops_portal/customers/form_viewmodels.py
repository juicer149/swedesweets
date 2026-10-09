from __future__ import annotations

from dataclasses import dataclass

from django.urls import reverse

from customers.models import Customer
from ops_portal.customers.forms import CustomerForm, InviteLoginForm
from ops_portal.customers.presentation import (
    customer_place_label,
    customer_status_icon,
    customer_status_key,
    customer_status_label,
)


@dataclass(frozen=True, slots=True)
class CustomerFormContext:
    form: CustomerForm | InviteLoginForm
    title: str
    submit_label: str
    cancel_url: str
    customer: Customer | None = None
    intro: str = ""

    def as_dict(self) -> dict[str, object]:
        context: dict[str, object] = {
            "intro": self.intro,
            "form": self.form,
            "customer": self.customer,
            "title": self.title,
            "submit_label": self.submit_label,
            "cancel_url": self.cancel_url,
        }

        if self.customer is not None:
            context |= {
                "status_key": customer_status_key(self.customer),
                "status_label": customer_status_label(self.customer),
                "status_icon": customer_status_icon(self.customer),
                "place_label": customer_place_label(self.customer),
            }

        return context


def build_create_customer_form_context(
    *,
    form: CustomerForm,
) -> CustomerFormContext:
    return CustomerFormContext(
        form=form,
        title="Add customer",
        submit_label="Add customer",
        cancel_url=reverse("ops_customers:index"),
    )


def build_edit_customer_form_context(
    *,
    form: CustomerForm,
    customer: Customer,
) -> CustomerFormContext:
    return CustomerFormContext(
        form=form,
        customer=customer,
        title=f"Edit {customer.name}",
        submit_label="Save customer",
        cancel_url=reverse("ops_customers:detail", kwargs={"customer_pk": customer.pk}),
    )


def build_invite_shop_form_context(
    *,
    form: CustomerForm,
) -> CustomerFormContext:
    return CustomerFormContext(
        form=form,
        title="Invite shop",
        submit_label="Send invitation",
        intro=(
            "We email the shop a link to choose a password. On first login "
            "they fill in their phone, address and city themselves, and can "
            "order once that is done."
        ),
        cancel_url=reverse("ops_customers:index"),
    )


def build_invite_login_form_context(
    *,
    form: InviteLoginForm,
    customer: Customer,
) -> CustomerFormContext:
    return CustomerFormContext(
        form=form,
        customer=customer,
        title=f"Invite {customer.name} to the portal",
        submit_label="Send invitation",
        cancel_url=reverse(
            "ops_customers:detail",
            kwargs={"customer_pk": customer.pk},
        ),
    )
