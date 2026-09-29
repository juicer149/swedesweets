from __future__ import annotations

import pytest
from django.core.cache import caches


_TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "tests-default",
    },
    # Tests must never read or wipe the file-based fake payments that
    # the local dev server relies on.
    "fake_payments": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "tests-fake-payments",
    },
}


def _clear_caches() -> None:
    for alias in _TEST_CACHES:
        caches[alias].clear()


@pytest.fixture(autouse=True)
def isolated_caches(settings):
    """Give every test its own empty in-memory caches."""

    settings.CACHES = _TEST_CACHES
    _clear_caches()

    yield

    _clear_caches()
