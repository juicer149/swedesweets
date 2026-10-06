"""Find Sweets: the public list of shops that sell SwedeSweets."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote_plus


@dataclass(frozen=True, slots=True)
class FindSweetsShop:
    name: str
    address: str
    maps_href: str


def maps_search_href(address: str) -> str:
    """The address on Google Maps (opens the app on a phone)."""

    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(address)}"
