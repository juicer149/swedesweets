#! src/swedesweets/domain/store.py
"""
Store entity.

Represents a customer store.

Design:
- Minimal for MVP
- Only identity and name

Future extensions may include:
- address
- contact information
- delivery preferences
"""

from dataclasses import dataclass
from uuid import UUID

from ._validation import require_non_empty_str, require_uuid


@dataclass(frozen=True)
class Store:
    """A retail store that places orders."""

    id: UUID
    name: str

    def __post_init__(self) -> None:
        require_uuid(self.id, field="store.id")
        require_non_empty_str(self.name, field="store.name")
