from dataclasses import dataclass

from accounts.domain.roles import StaffAccessLevel


@dataclass(frozen=True, slots=True)
class CreateStoreAccountCommand:
    username: str
    email: str
    password: str
    store_name: str
    phone: str
    address: str
    is_active: bool


@dataclass(frozen=True, slots=True)
class CreateStaffAccountCommand:
    username: str
    email: str
    password: str
    access_level: StaffAccessLevel
