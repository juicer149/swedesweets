#! src/swedesweets/domain/__init__.py
"""
Public domain API.

Purpose:
- Define what the outside world can import
- Hide internal module structure
- Expose a small and explicit domain surface
"""

from .draft import OrderDraft
from .errors import BusinessRuleError, DomainError, ValidationError
from .order import Order, OrderItem
from .product import Product
from .services import create_draft, create_order, finalize_draft, update_draft
from .store import Store
from .value_objects import ProductCode, Quantity

__all__ = [
    "Product",
    "Store",
    "Order",
    "OrderItem",
    "OrderDraft",
    "create_order",
    "create_draft",
    "update_draft",
    "finalize_draft",
    "ProductCode",
    "Quantity",
    "DomainError",
    "ValidationError",
    "BusinessRuleError",
]
