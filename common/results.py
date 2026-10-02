from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceResult[T]:
    item: T
    message: str
    created: bool
