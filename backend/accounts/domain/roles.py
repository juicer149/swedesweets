from dataclasses import dataclass
from enum import StrEnum


class StaffAccessLevel(StrEnum):
    RESTRICTED = "restricted"
    FULL = "full"

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        return [
            (cls.RESTRICTED, "Restricted"),
            (cls.FULL, "Full"),
        ]


class AccountRole(StrEnum):
    STORE = "store"
    RESTRICTED_STAFF = "restricted_staff"
    FULL_STAFF = "full_staff"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class RoleSpec:
    portal_route: str | None
    portal_template: str | None
    can_place_orders: bool
    can_view_staff_ops: bool
    can_access_admin: bool
    can_create_accounts: bool
    can_fulfill_orders: bool


ROLE_SPECS: dict[AccountRole, RoleSpec] = {
    AccountRole.STORE: RoleSpec(
        portal_route="accounts:store_portal",
        portal_template="accounts/store_portal.html",
        can_place_orders=True,
        can_view_staff_ops=False,
        can_access_admin=False,
        can_create_accounts=False,
        can_fulfill_orders=False,
    ),
    AccountRole.RESTRICTED_STAFF: RoleSpec(
        portal_route="accounts:restricted_staff_portal",
        portal_template="accounts/restricted_staff_portal.html",
        can_place_orders=False,
        can_view_staff_ops=True,
        can_access_admin=False,
        can_create_accounts=False,
        can_fulfill_orders=True,
    ),
    AccountRole.FULL_STAFF: RoleSpec(
        portal_route="accounts:staff_portal",
        portal_template="accounts/staff_portal.html",
        can_place_orders=False,
        can_view_staff_ops=True,
        can_access_admin=True,
        can_create_accounts=True,
        can_fulfill_orders=True,
    ),
    AccountRole.UNKNOWN: RoleSpec(
        portal_route=None,
        portal_template="accounts/no_store_connected.html",
        can_place_orders=False,
        can_view_staff_ops=False,
        can_access_admin=False,
        can_create_accounts=False,
        can_fulfill_orders=False,
    ),
}


def get_role_spec(role: AccountRole) -> RoleSpec:
    return ROLE_SPECS[role]
