"""A second look before prices change on the product edit form.

Saving changes to a price a variant already has (raised, lowered or
removed) asks first: the page comes back with the changes listed and asks
for the user's password again (accounts/password_again.py: a few wrong
tries lock it for a while), and saves only once it is given. A first
price (none before) is never asked about, so setting prices up the first
time stays quick.

settings.PRICE_CHANGE_CHECK (the PRICE_CHANGE_CHECK environment variable,
on by default) switches the check off, e.g. while prices are typed in.
Batch offers are to follow (docs/roadmap.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings

from accounts.password_again import PasswordAgainForm
from ops_portal.products.pricing_forms import PRICE_FIELDS, variant_amounts
from pricing.models import CommercialPrice


@dataclass(frozen=True, slots=True)
class PriceChange:
    variant_name: str
    channel_label: str
    currency: str
    old: Decimal
    # None: the price is removed.
    new: Decimal | None

    @property
    def percent(self) -> int | None:
        """The change in whole percent, signed (−20 is 20 % down)."""

        if self.new is None:
            return None

        return round((self.new - self.old) / self.old * 100)

    @property
    def percent_label(self) -> str:
        if self.percent is None:
            return "removed"

        return f"{self.percent:+d} %".replace("-", "−")


def check_is_on() -> bool:
    return bool(getattr(settings, "PRICE_CHANGE_CHECK", True))


def price_changes(
    *,
    prices_by_channel: dict[str, dict[int, CommercialPrice]],
    prices_form,
    variant_formset,
) -> list[PriceChange]:
    """The saved variants' prices that saving would change."""

    states = variant_formset.states_by_id
    changes: list[PriceChange] = []

    for row in variant_formset.ordered_forms_by_position:
        data = row.cleaned_data
        variant_id = data.get("variant_id")

        if variant_id is None or data.get("delete"):
            continue

        old = variant_amounts(
            prices_by_channel=prices_by_channel,
            variant_id=variant_id,
        )
        new = prices_form.prices_for(row)

        for field_name, channel, currency in PRICE_FIELDS:
            before = old[field_name]
            after = getattr(new, field_name)

            if before is not None and after != before:
                changes.append(
                    PriceChange(
                        variant_name=states[variant_id].variant.display_name,
                        channel_label=str(CommercialPrice.Channel(channel).label),
                        currency=currency,
                        old=before,
                        new=after,
                    )
                )

    return changes


@dataclass(frozen=True, slots=True)
class PriceCheck:
    """What the page asks about: the changes, and the password
    (accounts/password_again.py)."""

    changes: list[PriceChange]
    form: PasswordAgainForm
