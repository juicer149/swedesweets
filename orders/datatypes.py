"""
Order data transfer objects.

public API:
    whole_quantity(value: int) -> int
        -> Check that an order quantity is a whole number of stock units.

    BuyerInput
        -> Buyer data required by the order domain, independent of Customer storage.

    OrderLineInput.units(...)
        -> Build an order-line input in product stock units.

    OrderLineInput.resolve_product_id() -> int
        -> Resolve either product_id or product into product id.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from orders.errors import InvalidOrderOperation
from products.models import Product


def whole_quantity(value: int) -> int:
    """Order quantities count the product's stock unit (boxes, pieces):
    a whole number, never a weight."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidOrderOperation(
            "order line quantity must be a whole number"
        )

    return value


@dataclass(frozen=True, slots=True)
class BuyerInput:
    """Buyer data required to snapshot who an order is for.

    A buyer does not need to be a persisted Customer. The same contract can
    represent a business customer, a logged-in retail customer, or an
    anonymous retail buyer.
    """

    name: str
    email: str
    phone_number: str
    country: str
    city: str
    address_line: str
    postal_code: str = ""
    # The site language the buyer used ("en", "fr"); their mails are
    # written in it. Empty: the language active when the order is created.
    language: str = ""


@dataclass(frozen=True)
class OrderLineInput:
    """A product and how many of its stock unit to order."""

    quantity: int
    product_id: int | None = None
    product: Product | None = None

    def __post_init__(self) -> None:
        whole_quantity(self.quantity)

    @classmethod
    def units(
        cls,
        *,
        quantity: int,
        product: Product | None = None,
        product_id: int | None = None,
    ) -> Self:
        return cls(
            product=product,
            product_id=product_id,
            quantity=quantity,
        )

    def resolve_product_id(self) -> int:
        if (
            self.product_id is not None
            and self.product is not None
            and self.product_id != self.product.id
        ):
            raise InvalidOrderOperation(
                f"product_id ({self.product_id}) and "
                f"product ({self.product.id}) refer to different products"
            )

        if self.product_id is not None:
            return self.product_id

        if self.product is not None:
            return self.product.id

        raise InvalidOrderOperation("product_id or product is required")

