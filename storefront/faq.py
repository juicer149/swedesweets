"""Questions and answers for the FAQ pages.

One list for the public site, one for business customers. An item whose
answer is None is a question still waiting for an answer from
SwedeSweets: it is kept here as a reminder and not shown on the page.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _


@dataclass(frozen=True)
class FaqItem:
    """A question and its answer.

    contact     show how to reach us (mail, phone) under the answer
    link        a URL name to show as a link under the answer
    link_label  the link's text
    """

    question: str | Promise
    answer: str | Promise | None = None
    contact: bool = False
    link: str | None = None
    link_label: str | Promise = ""


BECOME_A_RESELLER = FaqItem(
    _("How do I become a reseller?"),
    _("Get in touch and we will set up an account for your shop."),
    contact=True,
)


PUBLIC_FAQ: tuple[FaqItem, ...] = (
    FaqItem(
        _("What can I buy online?"),
        _(
            "Our online shop sells SwedeSweets merch, and now and then candy "
            "offers, such as short-dated stock."
        ),
    ),
    FaqItem(
        _("Where do you deliver?"),
        _("We deliver online orders within Haute-Savoie (74)."),
    ),
    FaqItem(
        _("How do I pay?"),
        _(
            "By card. Payment is handled by SumUp, so your card details never "
            "reach us."
        ),
    ),
    FaqItem(
        _("Where can I find your candy in shops?"),
        _("The shops that sell our sweets are listed on Find Sweets."),
        link="public_site:find_sweets",
        link_label=_("Find Sweets"),
    ),
    BECOME_A_RESELLER,
    # Waiting for answers:
    FaqItem(_("How long does delivery take, and what does it cost?")),
    FaqItem(_("Can I return or exchange merch?")),
    FaqItem(_("Which sizes are available?")),
)


BUSINESS_FAQ: tuple[FaqItem, ...] = (
    BECOME_A_RESELLER,
    FaqItem(
        _("How do I log in?"),
        _(
            "With the username and password you received from us. If you have "
            "forgotten your password, use the link on the login page."
        ),
    ),
    FaqItem(
        _("Can I change my store's details?"),
        _(
            "Yes, under My account. Orders already placed keep the delivery "
            "details they were placed with."
        ),
    ),
    # Waiting for answers:
    FaqItem(_("Is there a minimum order?")),
    FaqItem(_("Which days do you deliver?")),
    FaqItem(_("How do invoices and payment terms work?")),
)


def answered(items: tuple[FaqItem, ...]) -> list[FaqItem]:
    """The items that have an answer, in order."""
    return [item for item in items if item.answer is not None]
