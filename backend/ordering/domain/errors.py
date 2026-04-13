class OrderingError(Exception):
    """Base class for ordering-related errors."""


class EmptyOrder(OrderingError):
    """Raised when an order contains no lines."""


class InvalidQuantity(OrderingError):
    """Raised when a quantity is invalid."""


class DuplicateProduct(OrderingError):
    """Raised when the same product appears more than once in an order."""


class StoreInactive(OrderingError):
    """Raised when an inactive store attempts to place an order."""


class InvalidProductSelection(OrderingError):
    """Raised when one or more selected products do not exist or are inactive."""


class InvalidOrderStatusTransition(OrderingError):
    """Raised when an order status change is not allowed."""
