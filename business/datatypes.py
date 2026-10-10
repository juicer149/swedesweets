from __future__ import annotations

from dataclasses import dataclass

from orders.datatypes import whole_quantity


@dataclass(frozen=True, slots=True)
class BusinessOfferLineInput:
    """One explicitly selected BUSINESS commercial offer, and how many of
    its product's stock unit."""

    commercial_offer_id: int
    quantity: int

    def __post_init__(self) -> None:
        whole_quantity(self.quantity)
