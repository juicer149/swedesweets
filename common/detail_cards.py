from __future__ import annotations

from dataclasses import dataclass

ACTION_METHOD_GET = "get"
ACTION_METHOD_POST = "post"

ACTION_TONE_SECONDARY = "secondary"
ACTION_TONE_PACK = "pack"
ACTION_TONE_DELIVER = "deliver"


@dataclass(frozen=True)


class DetailAction:
    label: str
    href: str = ""
    icon: str = ""
    method: str = ACTION_METHOD_GET
    tone: str = ACTION_TONE_SECONDARY
    client_behavior: str = ""
    is_disabled: bool = False


def build_secondary_get_action(
    *,
    label: str,
    href: str,
    icon: str = "",
) -> DetailAction:
    return DetailAction(
        label=label,
        href=href,
        icon=icon,
        method=ACTION_METHOD_GET,
        tone=ACTION_TONE_SECONDARY,
    )
