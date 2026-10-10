from __future__ import annotations


class ProductError(ValueError):
    """Base class for product domain errors."""


class InvalidProductData(ProductError):
    """Raised when product data violates product rules."""
