"""
The mails after SwedeSweets gives a shop's login another address.

public API:
    notify_login_email_change_on_commit(
        user=..., old_email=..., site_url=..., language=...
    )
        -> Once saved: a login that has a password gets a note at both the
           old and the new address (the old one, so a change nobody asked
           for does not go unnoticed). A login still waiting for its
           password (the invitation went to a wrong address) gets the
           invitation again, at the new address.

A mail that fails is logged, not raised: the change stands either way.
"""

from __future__ import annotations

import logging

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _

from accounts.invitations import send_account_invitation_on_commit
from common.contact import CONTACT_EMAIL

logger = logging.getLogger(__name__)


def notify_login_email_change_on_commit(
    *,
    user,
    old_email: str,
    site_url: str,
    language: str,
) -> bool:
    """Returns True when the invitation was sent again instead of the note
    (the login had no password yet)."""

    if not user.has_usable_password():
        send_account_invitation_on_commit(
            user=user,
            site_url=site_url,
            language=language,
        )
        return True

    user_pk = user.pk

    transaction.on_commit(
        lambda: send_login_email_changed(
            user_pk=user_pk,
            old_email=old_email,
            site_url=site_url,
            language=language,
        ),
        robust=True,
    )
    return False


def send_login_email_changed(
    *,
    user_pk: int,
    old_email: str,
    site_url: str,
    language: str,
) -> None:
    user = get_user_model().objects.get(pk=user_pk)

    try:
        with translation.override(language):
            context = {
                "new_email": user.email,
                "login_url": f"{site_url.rstrip('/')}{reverse('login')}",
                "contact_email": CONTACT_EMAIL,
            }
            subject = _("Your SwedeSweets login has changed")
            body = render_to_string("emails/login_email_changed.txt", context)
            html_body = render_to_string(
                "emails/login_email_changed.html",
                context,
            )
    except Exception:
        logger.exception("Could not write the login change mail for user %s", user_pk)
        return

    # One mail per address: neither sees the other in the recipients.
    for address in dict.fromkeys([user.email, old_email]):
        if not address:
            continue

        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=None,
                recipient_list=[address],
                html_message=html_body,
            )
        except Exception:
            logger.exception(
                "Could not send the login change mail for user %s", user_pk
            )
