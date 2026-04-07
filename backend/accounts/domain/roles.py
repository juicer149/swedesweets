from enum import StrEnum


class AccountType(StrEnum):
    """
    High-level account kind used by the account-creation workflow.
    """

    STAFF = "staff"
    STORE = "store"


class StaffAccessLevel(StrEnum):
    """
    Internal staff access levels.

    CURRENT MAPPING:
    - FULL -> is_staff=True, is_superuser=True
    - RESTRICTED -> is_staff=True, is_superuser=False

    This is a pragmatic MVP mapping and can later evolve into a richer
    permission/group model.
    """

    FULL = "full"
    RESTRICTED = "restricted"
