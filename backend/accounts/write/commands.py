from dataclasses import dataclass

from accounts.domain.roles import StaffAccessLevel


@dataclass(frozen=True, slots=True)
class CreateStoreAccountCommand:
    """
    Command for creating a store-linked account.

    This command describes the full input required to create:
    - a Django User
    - a linked Store
    """

    username: str
    email: str
    password: str
    store_name: str
    phone: str
    address: str
    is_active: bool


@dataclass(frozen=True, slots=True)
class CreateStaffAccountCommand:
    """
    Command for creating an internal staff account.

    The access level determines the current Django staff/superuser mapping.
    """

    username: str
    email: str
    password: str
    access_level: StaffAccessLevel
