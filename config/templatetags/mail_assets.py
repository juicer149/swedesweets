"""Whole addresses for pictures in mails.

A mail is read away from the site, so its pictures need the full address
(SITE_URL + the static path). Without SITE_URL there is no picture
rather than a broken one: the tag gives "".

    {% load mail_assets %}
    {% mail_asset_url "images/email-logo.png" as logo_url %}
"""

from __future__ import annotations

from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def mail_asset_url(path: str) -> str:
    if not settings.SITE_URL:
        return ""

    return f"{settings.SITE_URL}{static(path)}"
