from dataclasses import dataclass
from uuid import UUID, uuid4

from .errors import BusinessRuleError
from ._utils import ensure_unique


@dataclass(frozen=True)
class StoreProduct:
    id: UUID
    store_id: UUID
    product_id: UUID
    enabled: bool = True


@dataclass(frozen=True)
class StoreAssortment:
    store_id: UUID
    items: tuple[StoreProduct, ...]

    def __post_init__(self):
        ensure_unique(i.product_id for i in self.items)

    def includes(self, product_id: UUID) -> bool:
        return any(i.product_id == product_id and i.enabled for i in self.items)

    def add(self, product_id: UUID):
        if any(i.product_id == product_id for i in self.items):
            raise BusinessRuleError("product already exists")

        return StoreAssortment(
            store_id=self.store_id,
            items=self.items + (
                StoreProduct(
                    id=uuid4(),
                    store_id=self.store_id,
                    product_id=product_id,
                ),
            ),
        )
