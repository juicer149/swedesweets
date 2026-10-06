from __future__ import annotations

from dataclasses import dataclass

from django.urls import reverse

from accounts.roles import RoleSpec
from common.page_header import PageHeader, PageHeaderAction
from customers.models import Customer
from ops_portal.customers.access import can_create_customer
from ops_portal.customers.presentation import (
    customer_place_label,
    customer_status_icon,
)


@dataclass(frozen=True, slots=True)
class CustomerPageRow:
    customer: Customer
    detail_href: str

    @property
    def meta(self) -> str:
        """Phones: the grey line under the name (city, country)."""

        return customer_place_label(self.customer)

    @property
    def icon(self) -> str:
        return customer_status_icon(self.customer)


def build_customers_page_header(*, role_spec: RoleSpec) -> PageHeader:
    return PageHeader(
        title="Customers",
        title_id="customers-title",
        action=_build_add_customer_header_action(role_spec=role_spec),
    )


def _build_add_customer_header_action(
    *,
    role_spec: RoleSpec,
) -> PageHeaderAction | None:
    if not can_create_customer(role_spec=role_spec):
        return None

    return PageHeaderAction(
        label="Add customer",
        href=reverse("ops_customers:create"),
        aria_label="Add a new customer",
    )


def build_customer_page_rows(customers: list[Customer]) -> list[CustomerPageRow]:
    return [
        CustomerPageRow(
            customer=customer,
            detail_href=reverse(
                "ops_customers:detail",
                kwargs={"customer_pk": customer.pk},
            ),
        )
        for customer in customers
    ]
