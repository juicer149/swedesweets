class DomainError(Exception):
    """Base domain exception."""


class ValidationError(DomainError):
    """Invalid entity state."""
