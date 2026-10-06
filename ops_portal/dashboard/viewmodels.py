from __future__ import annotations

from dataclasses import dataclass

# -----------------------------------------------------------------------------
# Dashboard actions


@dataclass(frozen=True, slots=True)
class DashboardAction:
    label: str
    href: str
    css_class: str
    aria_label: str = ""
    icon: str = ""


# -----------------------------------------------------------------------------
# Dashboard queues


@dataclass(frozen=True, slots=True)
class DashboardQueueItem:
    title: str
    meta: str
    href: str
    action_label: str
    tone: str = "neutral"
    icon: str = ""


@dataclass(frozen=True, slots=True)
class DashboardQueue:
    """One queue as a row that slides open to its first few items."""

    key: str
    title: str
    count: int
    tone: str
    icon: str
    items: tuple[DashboardQueueItem, ...]
    view_all_href: str
    view_all_label: str
