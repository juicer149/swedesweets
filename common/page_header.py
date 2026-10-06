from __future__ import annotations

from dataclasses import dataclass

# A list page's "add" action: small, a yellow edge on no background, so
# it is easy to find without outweighing the list it sits by.
DEFAULT_PAGE_HEADER_ACTION_CLASS = (
    "button button--sm button--outline button--tone-place button--with-icon"
)


@dataclass(frozen=True)
class PageHeaderAction:
    label: str
    href: str
    icon: str = "plus"
    aria_label: str = ""
    css_class: str = DEFAULT_PAGE_HEADER_ACTION_CLASS


@dataclass(frozen=True)
class PageHeader:
    title: str
    title_id: str
    description: str = ""
    action: PageHeaderAction | None = None
