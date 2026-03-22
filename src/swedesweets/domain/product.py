from dataclasses import dataclass
from uuid import UUID

from .errors import ValidationError


@dataclass(frozen=True)
class Product:
    id: UUID
    name: str

    def __post_init__(self):
        if not self.name.strip():
            raise ValidationError("product name required")
