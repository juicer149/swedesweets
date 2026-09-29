from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.db import transaction

from retail.models import (
    RetailPostalArea,
    normalize_city,
    normalize_country_code,
    normalize_postal_code,
)


RETAIL_SERVICE_COUNTRY = "FR"
RETAIL_SERVICE_DEPARTMENT_PREFIX = "74"

GEO_API_COMMUNES_URL = (
    "https://geo.api.gouv.fr/departements/{department}/communes"
    "?fields=nom,codesPostaux&format=json"
)

POSTAL_AREA_SNAPSHOT_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / f"postal_areas_{RETAIL_SERVICE_DEPARTMENT_PREFIX}.json"
)

# Haute-Savoie has around 300 communes. A download far below this is
# treated as truncated rather than written over the snapshot.
MIN_EXPECTED_POSTAL_AREAS = 200


class PostalAreaFetchError(Exception):
    """Raised when upstream postal-area data cannot be trusted."""


@dataclass(frozen=True, slots=True)
class PostalAreaRecord:
    country_code: str
    postal_code: str
    city: str

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.country_code, self.postal_code, self.city)


@dataclass(frozen=True, slots=True)
class PostalAreaSyncResult:
    fetched: int
    created: int
    unchanged: int
    stale: tuple[PostalAreaRecord, ...]


def fetch_postal_areas() -> list[PostalAreaRecord]:
    """Return the current reference set of deliverable postal areas.

    Reads the committed snapshot of Haute-Savoie communes. The snapshot is
    refreshed deliberately with `refresh_retail_postal_area_snapshot`, so
    deploys never depend on an external API being reachable.

    Note: identity here is (country_code, postal_code, city). If an
    upstream source later renames a commune, that is treated as a new
    postal area (old key becomes stale, new key is created) rather than
    as a rename of the same destination. This is a deliberate v1
    limitation, not an oversight - see delivery-area sync design notes.
    """

    return read_postal_area_snapshot(
        path=POSTAL_AREA_SNAPSHOT_PATH,
    )


def download_postal_areas(
    *,
    timeout: float = 20.0,
) -> list[PostalAreaRecord]:
    """Download current communes and postal codes from geo.api.gouv.fr."""

    request = Request(
        GEO_API_COMMUNES_URL.format(
            department=RETAIL_SERVICE_DEPARTMENT_PREFIX,
        ),
        headers={
            "Accept": "application/json",
            "User-Agent": "SwedeSweets postal-area snapshot",
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except (
        URLError,
        TimeoutError,
        json.JSONDecodeError,
    ) as exc:
        raise PostalAreaFetchError(
            f"could not download postal areas: {exc}"
        ) from exc

    records = records_from_geo_api_communes(
        payload
    )

    if len(records) < MIN_EXPECTED_POSTAL_AREAS:
        raise PostalAreaFetchError(
            f"downloaded only {len(records)} postal areas, expected at "
            f"least {MIN_EXPECTED_POSTAL_AREAS}"
        )

    return records


def records_from_geo_api_communes(
    payload: Any,
) -> list[PostalAreaRecord]:
    """Flatten geo.api.gouv.fr communes into one record per postal code."""

    if not isinstance(payload, list):
        raise PostalAreaFetchError(
            "unexpected geo API payload: expected a list of communes"
        )

    records: list[PostalAreaRecord] = []

    for commune in payload:
        if not isinstance(commune, dict):
            raise PostalAreaFetchError(
                "unexpected geo API payload: commune is not an object"
            )

        name = commune.get("nom")
        postal_codes = commune.get("codesPostaux")

        if not isinstance(name, str) or not isinstance(postal_codes, list):
            raise PostalAreaFetchError(
                f"unexpected geo API commune: {commune!r}"
            )

        for postal_code in postal_codes:
            postal_code = str(postal_code)

            if not postal_code.startswith(
                RETAIL_SERVICE_DEPARTMENT_PREFIX
            ):
                continue

            records.append(
                _normalize_record(
                    country_code=RETAIL_SERVICE_COUNTRY,
                    postal_code=postal_code,
                    city=name,
                )
            )

    _validate_records(records)

    return _sorted(
        _deduplicate(records)
    )


def write_postal_area_snapshot(
    records: list[PostalAreaRecord],
    *,
    path: Path = POSTAL_AREA_SNAPSHOT_PATH,
) -> None:
    """Write records as a stable, diff-friendly JSON snapshot."""

    _validate_records(records)

    area_lines = ",\n".join(
        "    "
        + json.dumps(
            [record.postal_code, record.city],
            ensure_ascii=False,
        )
        for record in _sorted(records)
    )

    header = json.dumps(
        {
            "source": GEO_API_COMMUNES_URL.format(
                department=RETAIL_SERVICE_DEPARTMENT_PREFIX,
            ),
            "country_code": RETAIL_SERVICE_COUNTRY,
            "fetched_on": date.today().isoformat(),
        },
        ensure_ascii=False,
    )[:-1]

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        f'{header}, "areas": [\n{area_lines}\n]}}\n',
        encoding="utf-8",
    )


def read_postal_area_snapshot(
    *,
    path: Path,
) -> list[PostalAreaRecord]:
    try:
        data = json.loads(
            path.read_text(encoding="utf-8")
        )
    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:
        raise PostalAreaFetchError(
            f"could not read postal-area snapshot {path}: {exc}"
        ) from exc

    areas = data.get("areas") if isinstance(data, dict) else None

    if not isinstance(areas, list):
        raise PostalAreaFetchError(
            f"postal-area snapshot {path} has no areas list"
        )

    country_code = data.get(
        "country_code",
        RETAIL_SERVICE_COUNTRY,
    )

    records = []

    for area in areas:
        if (
            not isinstance(area, list)
            or len(area) != 2
            or not all(isinstance(value, str) for value in area)
        ):
            raise PostalAreaFetchError(
                f"invalid postal-area snapshot entry: {area!r}"
            )

        postal_code, city = area

        records.append(
            _normalize_record(
                country_code=country_code,
                postal_code=postal_code,
                city=city,
            )
        )

    _validate_records(records)

    return _deduplicate(records)


@transaction.atomic
def sync_retail_postal_areas() -> PostalAreaSyncResult:
    """Add newly known postal areas without touching existing rows.

    Fetch and validation happen before this function is called
    (`fetch_postal_areas` runs first, outside any lock), so no network
    I/O occurs inside the transaction.

    Existing rows, including their local `enabled` override, are never
    modified or deleted. Postal areas that used to be known locally but
    are no longer present upstream are reported as stale for manual
    review; they are not disabled or removed automatically.
    """

    fetched_records = fetch_postal_areas()

    fetched_by_key = {
        record.key: record
        for record in fetched_records
    }

    existing_keys = set(
        RetailPostalArea.objects
        .values_list("country_code", "postal_code", "city")
    )

    new_keys = set(fetched_by_key) - existing_keys
    stale_keys = existing_keys - set(fetched_by_key)

    if new_keys:
        RetailPostalArea.objects.bulk_create(
            [
                RetailPostalArea(
                    country_code=key[0],
                    postal_code=key[1],
                    city=key[2],
                    enabled=True,
                )
                for key in new_keys
            ]
        )

    stale_records = tuple(
        PostalAreaRecord(
            country_code=key[0],
            postal_code=key[1],
            city=key[2],
        )
        for key in sorted(stale_keys)
    )

    return PostalAreaSyncResult(
        fetched=len(fetched_by_key),
        created=len(new_keys),
        unchanged=len(fetched_by_key) - len(new_keys),
        stale=stale_records,
    )


def _normalize_record(
    *,
    country_code: str,
    postal_code: str,
    city: str,
) -> PostalAreaRecord:
    return PostalAreaRecord(
        country_code=normalize_country_code(country_code),
        postal_code=normalize_postal_code(postal_code),
        city=normalize_city(city),
    )


def _validate_records(
    records: list[PostalAreaRecord],
) -> None:
    if not records:
        raise PostalAreaFetchError(
            "postal-area fetch returned no records"
        )

    for record in records:
        if record.country_code != RETAIL_SERVICE_COUNTRY:
            raise PostalAreaFetchError(
                f"postal area {record.postal_code} is outside the "
                f"supported country {RETAIL_SERVICE_COUNTRY}"
            )

        if not record.postal_code.startswith(
            RETAIL_SERVICE_DEPARTMENT_PREFIX
        ):
            raise PostalAreaFetchError(
                f"postal area {record.postal_code} is outside "
                f"departement {RETAIL_SERVICE_DEPARTMENT_PREFIX}"
            )

        if not record.city:
            raise PostalAreaFetchError(
                f"postal area {record.postal_code} is missing a city"
            )


def _deduplicate(
    records: list[PostalAreaRecord],
) -> list[PostalAreaRecord]:
    deduplicated: dict[tuple[str, str, str], PostalAreaRecord] = {}

    for record in records:
        deduplicated[record.key] = record

    return list(deduplicated.values())


def _sorted(
    records: list[PostalAreaRecord],
) -> list[PostalAreaRecord]:
    return sorted(
        records,
        key=lambda record: (record.postal_code, record.city),
    )
