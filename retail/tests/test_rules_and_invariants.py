from __future__ import annotations

from decimal import Decimal

import pytest

from retail.rules import (
    MAX_RETAIL_LINE_QUANTITY,
    MAX_RETAIL_ORDER_TOTAL,
    MIN_RETAIL_LINE_QUANTITY,
    find_retail_destination,
    list_retail_cities_for_postal_code,
    is_supported_retail_destination,
    is_valid_retail_line_quantity,
    is_valid_retail_order_total,
    normalize_city_for_matching,
)
from retail.tests.factories import retail_postal_area_factory


@pytest.mark.django_db
def test_known_enabled_destination_is_supported():
    retail_postal_area_factory(
        country_code="FR",
        postal_code="74000",
        city="Annecy",
    )

    assert is_supported_retail_destination(
        country_code="FR",
        postal_code="74000",
        city="Annecy",
    )

@pytest.mark.django_db
@pytest.mark.parametrize(
    ("country_code", "postal_code", "city"),
    [
        ("SE", "74000", "Annecy"),
        ("FR", "75001", "Annecy"),
        ("FR", "74000", "Paris"),
    ],
)
def test_destination_requires_matching_country_postal_code_and_city(
    country_code: str,
    postal_code: str,
    city: str,
):
    retail_postal_area_factory(
        country_code="FR",
        postal_code="74000",
        city="Annecy",
    )

    assert not is_supported_retail_destination(
        country_code=country_code,
        postal_code=postal_code,
        city=city,
    )

@pytest.mark.django_db
def test_disabled_destination_is_not_supported():
    retail_postal_area_factory(
        country_code="FR",
        postal_code="74000",
        city="Annecy",
        enabled=False,
    )

    assert not is_supported_retail_destination(
        country_code="FR",
        postal_code="74000",
        city="Annecy",
    )

@pytest.mark.django_db
def test_destination_matching_ignores_country_and_city_case():
    retail_postal_area_factory()

    assert is_supported_retail_destination(
        country_code="fr",
        postal_code="74000",
        city="annecy",
    )

@pytest.mark.django_db
def test_destination_matching_ignores_surrounding_whitespace():
    retail_postal_area_factory()

    assert is_supported_retail_destination(
        country_code=" FR ",
        postal_code=" 74000 ",
        city=" Annecy ",
    )

@pytest.mark.django_db
@pytest.mark.parametrize(
    ("country_code", "postal_code", "city"),
    [
        ("", "74000", "Annecy"),
        ("FR", "", "Annecy"),
        ("FR", "74000", ""),
        (" ", "74000", "Annecy"),
        ("FR", " ", "Annecy"),
        ("FR", "74000", " "),
    ],
)
def test_blank_destination_component_is_rejected(
    country_code: str,
    postal_code: str,
    city: str,
):
    retail_postal_area_factory()

    assert not is_supported_retail_destination(
        country_code=country_code,
        postal_code=postal_code,
        city=city,
    )

@pytest.mark.parametrize(
    "quantity",
    [
        MIN_RETAIL_LINE_QUANTITY,
        MAX_RETAIL_LINE_QUANTITY,
    ],
)
def test_retail_line_quantity_accepts_boundaries(quantity: int):
    assert is_valid_retail_line_quantity(quantity)

@pytest.mark.parametrize(
    "quantity",
    [
        MIN_RETAIL_LINE_QUANTITY - 1,
        MAX_RETAIL_LINE_QUANTITY + 1,
    ],
)
def test_retail_line_quantity_rejects_values_outside_boundaries(
    quantity: int,
):
    assert not is_valid_retail_line_quantity(quantity)

@pytest.mark.parametrize(
    "total",
    [
        Decimal("0.01"),
        MAX_RETAIL_ORDER_TOTAL,
    ],
)
def test_retail_order_total_accepts_valid_boundaries(total: Decimal):
    assert is_valid_retail_order_total(total)

@pytest.mark.parametrize(
    "total",
    [
        Decimal("0.00"),
        Decimal("-0.01"),
        MAX_RETAIL_ORDER_TOTAL + Decimal("0.01"),
    ],
)
def test_retail_order_total_rejects_invalid_values(total: Decimal):
    assert not is_valid_retail_order_total(total)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Chamonix-Mont-Blanc", "chamonix mont blanc"),
        ("  CHAMONIX   MONT BLANC ", "chamonix mont blanc"),
        ("Argentière", "argentiere"),
        ("St Gervais-les-Bains", "saint gervais les bains"),
        ("St. Gervais les Bains", "saint gervais les bains"),
        ("L'Abbaye", "l abbaye"),
    ],
)
def test_normalize_city_for_matching(value: str, expected: str):
    assert normalize_city_for_matching(value) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "typed_city",
    [
        "chamonix mont blanc",
        "CHAMONIX-MONT-BLANC",
        "Chamonix Mont-Blanc",
    ],
)
def test_destination_matching_tolerates_spelling_variants(typed_city: str):
    retail_postal_area_factory(
        postal_code="74400",
        city="Chamonix-Mont-Blanc",
    )

    destination = find_retail_destination(
        country_code="FR",
        postal_code="74 400",
        city=typed_city,
    )

    assert destination is not None
    assert destination.city == "Chamonix-Mont-Blanc"


@pytest.mark.django_db
def test_destination_matching_still_rejects_other_towns():
    retail_postal_area_factory(
        postal_code="74400",
        city="Chamonix-Mont-Blanc",
    )

    assert find_retail_destination(
        country_code="FR",
        postal_code="74400",
        city="Chamonix",
    ) is None


@pytest.mark.django_db
def test_list_cities_for_postal_code_returns_enabled_towns_sorted():
    retail_postal_area_factory(postal_code="74310", city="Servoz")
    retail_postal_area_factory(postal_code="74310", city="Les Houches")
    retail_postal_area_factory(
        postal_code="74310",
        city="Disabled Town",
        enabled=False,
    )

    assert list_retail_cities_for_postal_code(
        country_code="FR",
        postal_code="74310",
    ) == ["Les Houches", "Servoz"]
