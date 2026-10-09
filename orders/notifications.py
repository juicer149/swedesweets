"""
Mails about a placed order: the buyer's confirmation (HTML, with the logo,
and plain text), and a note to the shop (ORDER_NOTIFICATION_EMAILS, plain).

public API:
    send_order_placed_mails_on_commit(order)
        -> Queue both mails for when the current transaction commits.
           Business: when a shop places its cart. Retail: when the
           payment has gone through.

    send_order_placed_mails(order_id=...)
        -> Send them now.

A mail that fails is logged, never raised: the order stands whether or not
the mail goes out (the shop still sees it in ops).
"""

from __future__ import annotations

import logging
from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _

from orders.models import Order

logger = logging.getLogger(__name__)

# The shop's note is for the people behind it, not a customer.
STAFF_LANGUAGE = "en"


def send_order_placed_mails_on_commit(order: Order) -> None:
    order_id = order.pk

    transaction.on_commit(
        lambda: send_order_placed_mails(order_id=order_id),
        robust=True,
    )


def send_order_placed_mails(*, order_id: int) -> None:
    order = (
        Order.objects
        .select_related("customer")
        .prefetch_related("lines__product")
        .get(pk=order_id)
    )

    for send in (_send_buyer_confirmation, _send_staff_notification):
        try:
            send(order)
        except Exception:
            logger.exception(
                "Could not send %s for order %s",
                send.__name__,
                order.pk,
            )


def _send_buyer_confirmation(order: Order) -> None:
    recipient = order.buyer_email

    if not recipient:
        return

    language = order.buyer_language_snapshot or settings.LANGUAGE_CODE

    with translation.override(language):
        is_business = order.channel == Order.Channel.BUSINESS
        context = _mail_context(order)
        context["account_url"] = (
            _absolute_url(reverse("business_portal:index") + "?tab=orders")
            if is_business
            else ""
        )

        subject = (
            _("Order #%(number)s received – SwedeSweets")
            if is_business
            else _("Thank you for your order #%(number)s – SwedeSweets")
        ) % {"number": order.pk}

        context["language"] = language
        context["logo_url"] = _absolute_url(static("images/email-logo.png"))

        body = render_to_string(
            "emails/order_placed_buyer.txt",
            context,
        )
        html_body = render_to_string(
            "emails/order_placed_buyer.html",
            context,
        )

    send_mail(
        subject=subject,
        message=body,
        from_email=None,
        recipient_list=[recipient],
        html_message=html_body,
    )


def _send_staff_notification(order: Order) -> None:
    recipients = settings.ORDER_NOTIFICATION_EMAILS

    if not recipients:
        return

    with translation.override(STAFF_LANGUAGE):
        context = _mail_context(order)
        context["ops_url"] = _absolute_url(
            reverse("ops_orders:detail", kwargs={"order_id": order.pk})
        )

        subject = (
            f"New order #{order.pk} – "
            f"{order.get_channel_display()} – {order.buyer_name}"
        )

        body = render_to_string(
            "emails/order_placed_staff.txt",
            context,
        )

    send_mail(
        subject=subject,
        message=body,
        from_email=None,
        recipient_list=list(recipients),
    )


def _mail_context(order: Order) -> dict:
    lines = [
        {
            "quantity": line.quantity_in_units,
            "name": line.product.display_name,
            "total": _price_label(line.line_total),
        }
        for line in order.lines.all()
    ]

    return {
        "order": order,
        "is_business": order.channel == Order.Channel.BUSINESS,
        "lines": lines,
        "total": _price_label(order.total),
    }


def _price_label(amount: Decimal | None) -> str:
    if amount is None:
        return ""

    return f"€{amount:.2f}"


def _absolute_url(path: str) -> str:
    """A link for a mail, which needs the whole address (SITE_URL).

    Without SITE_URL there is no link: better none than a broken one."""

    if not settings.SITE_URL:
        return ""

    return f"{settings.SITE_URL}{path}"
