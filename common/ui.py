"""
Reusable presentation value objects.

This module contains small immutable objects that describe how already-known
domain data should be presented in templates.

It should not query the database.
It should not own business rules.
It should not know about HTTP requests.

Good use:
    Order status "placed" -> warning tone
    8 units -> "8 units left", low/safe/empty quantity class

Bad use:
    Fetch orders from database
    Decide whether an order may be packed
    Change model state

The purpose is to keep templates dumb and predictable. Selectors/viewmodels build
these objects; templates render them.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)


class UiTone:
    """Semantic UI tone.

    A tone is presentation language, not domain language.

    Domain:
        placed
        packed
        active
        depleted

    Presentation:
        warning
        info
        success
        danger
        muted
    """

    key: str
    label: str
    text_class: str


@dataclass(frozen=True)


class UiText:
    """Renderable text atom.

    If href is empty, templates render this as a span.
    If href exists, templates render this as an anchor.

    label is rendered above text.
    subtext is rendered below text.
    """

    text: str
    href: str = ""
    css_class: str = "ui-text"
    target: str = ""
    rel: str = ""
    aria_label: str = ""
    label: str = ""
    label_class: str = ""
    subtext: str = ""
    subtext_class: str = ""
    icon: str = ""
    icon_class: str = "ui-text__icon"


@dataclass(frozen=True)


class QuantityInfo:
    value: int
    level: str
    label: str
    css_class: str


@dataclass(frozen=True)


class StatusPresentation:
    value: str
    label: str
    tone: UiTone
    text: UiText
    button_class: str = ""
    href: str = ""
    icon: str = ""


TONE_MUTED = UiTone(
    key="muted",
    label="Muted",
    text_class="status-text--muted",
)

TONE_WARNING = UiTone(
    key="warning",
    label="Warning",
    text_class="status-text--warning",
)

TONE_INFO = UiTone(
    key="info",
    label="Info",
    text_class="status-text--info",
)

TONE_SUCCESS = UiTone(
    key="success",
    label="Success",
    text_class="status-text--success",
)

TONE_DANGER = UiTone(
    key="danger",
    label="Danger",
    text_class="status-text--danger",
)


def build_quantity_info(
    *,
    quantity: int,
    low_threshold: int = 10,
    running_low_threshold: int | None = None,
) -> QuantityInfo:
    """Return presentation info for a stock quantity.

    empty (red) at zero, low (red) at or under low_threshold, running low
    (orange) at or under running_low_threshold when given, safe (green)
    above. Callers pass the inventory.low_stock thresholds.
    """

    label = f"{quantity} units left"

    if quantity <= 0:
        return QuantityInfo(
            value=quantity,
            level="empty",
            label="0 units left",
            css_class="quantity-text quantity-text--empty",
        )

    if quantity <= low_threshold:
        return QuantityInfo(
            value=quantity,
            level="low",
            label=label,
            css_class="quantity-text quantity-text--low",
        )

    if (
        running_low_threshold is not None
        and quantity <= running_low_threshold
    ):
        return QuantityInfo(
            value=quantity,
            level="running_low",
            label=label,
            css_class="quantity-text quantity-text--running-low",
        )

    return QuantityInfo(
        value=quantity,
        level="safe",
        label=label,
        css_class="quantity-text quantity-text--safe",
    )
