from __future__ import annotations

import re
import unicodedata
from datetime import timedelta
from decimal import Decimal

from retail.models import RetailPostalArea

MIN_RETAIL_LINE_QUANTITY = 1
MAX_RETAIL_LINE_QUANTITY = 20

MAX_RETAIL_ORDER_LINES = 20
MAX_RETAIL_ORDER_TOTAL = Decimal("1000.00")

RETAIL_CHECKOUT_WINDOW = timedelta(minutes=90)
RETAIL_PAYMENT_RESERVATION_WINDOW = timedelta(minutes=35)

_CITY_SEPARATORS = re.compile(r"[-'’_.,/]")

_CITY_WORD_ALIASES = {
    "st": "saint",
    "ste": "sainte",
}


def normalize_city_for_matching(
    value: str,
) -> str:
    """Return a comparison key for a town name.

    Case, accents, hyphens, apostrophes and repeated whitespace are ignored,
    and common abbreviations are expanded, so that "chamonix mont blanc",
    "CHAMONIX-MONT-BLANC" and "St Gervais les Bains" match their official
    spellings.
    """

    decomposed = unicodedata.normalize(
        "NFKD",
        value,
    )
    without_accents = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )
    spaced = _CITY_SEPARATORS.sub(
        " ",
        without_accents.casefold(),
    )

    return " ".join(
        _CITY_WORD_ALIASES.get(word, word)
        for word in spaced.split()
    )


def normalize_postal_code_for_matching(
    value: str,
) -> str:
    return "".join(
        value.split()
    )


def list_retail_cities_for_postal_code(
    *,
    country_code: str,
    postal_code: str,
) -> list[str]:
    """Return official town names deliverable under one postal code."""

    country = country_code.strip().upper()
    postal = normalize_postal_code_for_matching(
        postal_code
    )

    if not country or not postal:
        return []

    return list(
        RetailPostalArea.objects
        .filter(
            country_code=country,
            postal_code=postal,
            enabled=True,
        )
        .order_by("city")
        .values_list(
            "city",
            flat=True,
        )
    )


def find_retail_destination(
    *,
    country_code: str,
    postal_code: str,
    city: str,
) -> RetailPostalArea | None:
    """Return the enabled postal area matching a buyer-entered destination."""

    country = country_code.strip().upper()
    postal = normalize_postal_code_for_matching(
        postal_code
    )
    city_key = normalize_city_for_matching(
        city
    )

    if not country or not postal or not city_key:
        return None

    candidates = RetailPostalArea.objects.filter(
        country_code=country,
        postal_code=postal,
        enabled=True,
    )

    for area in candidates:
        if normalize_city_for_matching(area.city) == city_key:
            return area

    return None


def is_supported_retail_destination(
    *,
    country_code: str,
    postal_code: str,
    city: str,
) -> bool:
    """Return whether SwedeSweets currently delivers to this destination."""

    return find_retail_destination(
        country_code=country_code,
        postal_code=postal_code,
        city=city,
    ) is not None


def is_valid_retail_line_quantity(quantity: int) -> bool:
    return MIN_RETAIL_LINE_QUANTITY <= quantity <= MAX_RETAIL_LINE_QUANTITY


def is_valid_retail_order_total(total: Decimal) -> bool:
    return Decimal("0.00") < total <= MAX_RETAIL_ORDER_TOTAL
