from __future__ import annotations

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _isolated_cache():
    """Give every test an empty cache.

    The database is rolled back between tests but the cache is not, so
    state kept in the cache (such as fake payments) would otherwise leak
    from one test into the next.
    """

    cache.clear()
    yield
    cache.clear()
