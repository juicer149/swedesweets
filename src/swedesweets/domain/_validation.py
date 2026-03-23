#! src/swedesweets/domain/_validation.py
"""
Validation helpers.

Purpose:
- Centralize low-level validation logic
- Avoid repeating structural checks across entities
- Keep entities focused on domain intent

Important:
- These helpers validate structure, not business rules
- Business rules belong in services or policies
"""

from uuid import UUID

from .errors import ValidationError


def require_uuid(value, *, field: str) -> None:
    if not isinstance(value, UUID):
        raise ValidationError(f"{field} must be UUID")


def require_non_empty_str(value, *, field: str) -> None:
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be str")

    if not value.strip():
        raise ValidationError(f"{field} required")


def require_max_length(value: str, *, field: str, max_length: int) -> None:
    if len(value) > max_length:
        raise ValidationError(f"{field} too long")
