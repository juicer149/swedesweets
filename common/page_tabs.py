"""Tabs on a calm page (layouts/detail.html, includes/ui/page_tabs.html).

A detail page and its edit form share one shape: the heading, a section
nav of tabs, and under it the active tab's content with its own actions.
Each tab is a template; the page lists them in order and the first one
opens unless the URL names another (#pricing) or a tab holds form errors
(tabs.js).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PageTab:
    key: str
    label: str
    template: str
    icon: str = ""


@dataclass(frozen=True, slots=True)
class TabAction:
    """An action at the right of the section nav, shown while its tab is
    open (tabs.js): the product page's Edit leads to the product's form on
    the Product tab, to the catalog's on the Catalog tab."""

    tab: str
    href: str
    label: str = "Edit"
    icon: str = "pencil"
