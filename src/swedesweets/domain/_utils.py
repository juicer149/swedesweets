from typing import Iterable
from uuid import UUID

from .errors import ValidationError


def ensure_unique(ids: Iterable[UUID]) -> None:
    seen = set()
    for i in ids:
        if i in seen:
            raise ValidationError("duplicate id")
        seen.add(i)
