from dataclasses import dataclass
from uuid import UUID

from .types import DeliveryWindow
from .errors import ValidationError


@dataclass(frozen=True, slots=True)
class Store:
    id: UUID
    name: str
    address: str | None = None
    delivery_window: DeliveryWindow | None = None

    def __post_init__(self):

        if not self.name:
            raise ValidationError("store name required")
