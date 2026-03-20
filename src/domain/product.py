from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from .errors import ValidationError

# kan nog ta bort detta från domain?
class ProductCategory(StrEnum):
    CANDY = "candy"
    CHIPS = "chips"
    DIP = "dip"
    DRINK = "drink"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class Product:
    id: UUID
    name: str
    category: ProductCategory
    # behövs verkligne active med? isåfall endast för supplier om det skulle vara slut i lagret. men för store så borde ju endast de produkter som dem har i sitt sortement vara aktiva och alla andra oaktiva och då ser jag inte meningen i att ens behöva ha flaggan,om den är lagrad så har dem det i sortementet.
    active: bool = True

    def __post_init__(self):

        if not self.name:
            raise ValidationError("product name required")
