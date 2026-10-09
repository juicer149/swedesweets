"""
The invitation a new account gets instead of a password typed by staff.

public API:
    send_account_invitation_on_commit(user=..., site_url=..., language=...)
        -> Once the account is saved, mail its address a link to choose
           a password (Django's reset link: valid PASSWORD_RESET_TIMEOUT,
           three days by default). An expired link is no dead end:
           "Forgot password?" on the login page sends a new one.

A mail that fails is logged, not raised: the account exists either way,
and the person can still use "Forgot password?".
"""

from __future__ import annotations

import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import translation
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


def send_account_invitation_on_commit(
    *,
    user,
    site_url: str,
    language: str,
) -> None:
    user_pk = user.pk

    transaction.on_commit(
        lambda: send_account_invitation(
            user_pk=user_pk,
            site_url=site_url,
            language=language,
        ),
        robust=True,
    )


def send_account_invitation(
    *,
    user_pk: int,
    site_url: str,
    language: str,
) -> None:
    user = get_user_model().objects.get(pk=user_pk)

    try:
        with translation.override(language):
            path = reverse(
                "password_reset_confirm",
                kwargs={
                    "uidb64": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": default_token_generator.make_token(user),
                },
            )
            context = {
                "user": user,
                "set_password_url": f"{site_url.rstrip('/')}{path}",
                "login_url": f"{site_url.rstrip('/')}{reverse('login')}",
            }

            subject = _("Your SwedeSweets account")
            body = render_to_string("emails/account_invitation.txt", context)
            html_body = render_to_string(
                "emails/account_invitation.html",
                context,
            )

        send_mail(
            subject=subject,
            message=body,
            from_email=None,
            recipient_list=[user.email],
            html_message=html_body,
        )
    except Exception:
        logger.exception("Could not send the invitation to user %s", user.pk)
