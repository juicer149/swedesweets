from __future__ import annotations

from accounts.roles import Capability, RoleSpec
from customers.models import Customer

CAPABILITIES = frozenset(
    {
        Capability.VIEW_CUSTOMERS,
        Capability.CREATE_CUSTOMERS,
        Capability.EDIT_CUSTOMERS,
    }
)


VIEW_CAPABILITIES = {
    "ops_customers:index": Capability.VIEW_CUSTOMERS,
    "ops_customers:detail": Capability.VIEW_CUSTOMERS,
    "ops_customers:create": Capability.CREATE_CUSTOMERS,
    "ops_customers:edit": Capability.EDIT_CUSTOMERS,
    # An invitation creates a login: account management.
    "ops_customers:invite": Capability.MANAGE_ACCOUNTS,
    "ops_customers:invite_login": Capability.MANAGE_ACCOUNTS,
}


def can_create_customer(*, role_spec: RoleSpec) -> bool:
    return role_spec.allows(Capability.CREATE_CUSTOMERS)


def can_edit_customer(
    *,
    customer: Customer,
    role_spec: RoleSpec,
) -> bool:
    return role_spec.allows(Capability.EDIT_CUSTOMERS)


def can_invite_logins(*, role_spec: RoleSpec) -> bool:
    return role_spec.allows(Capability.MANAGE_ACCOUNTS)
