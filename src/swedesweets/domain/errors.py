class DomainError(Exception):
    """Base class for domain errors."""


class ValidationError(DomainError):
    """Raised when an invariant/value object validation fails."""


class RelationshipError(DomainError):
    """Raised when objects that should be related are not (e.g. wrong IDs)."""
