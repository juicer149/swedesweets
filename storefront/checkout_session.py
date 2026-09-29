"""Session ownership of retail checkouts for anonymous buyers.

A checkout id in the URL is not enough to view the checkout: the buyer's
session must have created it. This keeps buyer details private even if a
checkout URL is shared or leaks through browser history.
"""

from __future__ import annotations

from uuid import UUID

from django.http import HttpRequest

CHECKOUT_IDS_SESSION_KEY = "retail_checkout_ids"
CHECKOUT_DETAILS_SESSION_KEY = "retail_checkout_details"
MAX_REMEMBERED_CHECKOUTS = 5


def remember_checkout(
    request: HttpRequest,
    *,
    checkout_id: UUID,
) -> None:
    value = str(checkout_id)

    checkout_ids = [
        existing
        for existing in request.session.get(
            CHECKOUT_IDS_SESSION_KEY,
            [],
        )
        if existing != value
    ]
    checkout_ids.append(value)

    request.session[CHECKOUT_IDS_SESSION_KEY] = checkout_ids[
        -MAX_REMEMBERED_CHECKOUTS:
    ]


def owns_checkout(
    request: HttpRequest,
    *,
    checkout_id: UUID,
) -> bool:
    return str(checkout_id) in request.session.get(
        CHECKOUT_IDS_SESSION_KEY,
        [],
    )


def remember_checkout_details(
    request: HttpRequest,
    *,
    details: dict[str, str],
) -> None:
    request.session[CHECKOUT_DETAILS_SESSION_KEY] = details


def get_remembered_checkout_details(
    request: HttpRequest,
) -> dict[str, str] | None:
    return request.session.get(
        CHECKOUT_DETAILS_SESSION_KEY,
    )
