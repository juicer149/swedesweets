from dataclasses import dataclass
from datetime import time


@dataclass(frozen=True, slots=True)
class DeliveryWindow:
    weekday: int
    start: time
    end: time

    def __post_init__(self):

        if not 0 <= self.weekday <= 6:
            raise ValueError("weekday must be 0-6")

        if self.start >= self.end:
            raise ValueError("invalid delivery window")
