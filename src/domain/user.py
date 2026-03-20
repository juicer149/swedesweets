from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from .errors import ValidationError


class UserRole(StrEnum):
    """
    Role of a system user.
    """

    SUPPLIER = "supplier"
    STORE = "store"


@dataclass(frozen=True, slots=True)
class User:
    id: UUID
    username: str
    password_hash: bytes
    role: UserRole

    def __post_init__(self):

        if not self.username:
            raise ValidationError("username required")
