"""Small HTTP helpers shared by the portals."""

from __future__ import annotations


def wants_json(request) -> bool:
    """Whether a page's script asked for JSON (Accept: application/json)
    rather than a page: the same view answers both."""

    return "application/json" in request.headers.get("Accept", "")
