from dataclasses import dataclass
from uuid import UUID

from .errors import ValidationError


@dataclass(frozen=True)
class Store:
    id: UUID
    name: str

    def __post_init__(self):
        if not self.name.strip():
            raise ValidationError("store name required")
