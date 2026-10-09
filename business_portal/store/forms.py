from __future__ import annotations

from django import forms
from django.utils.html import format_html
from django.utils.translation import gettext, gettext_lazy

from common.contact import CONTACT_EMAIL
from common.form_layout import set_form_field_layout
from customers.models import (
    CUSTOMER_COUNTRY_LABELS,
    MAX_CUSTOMER_ADDRESS_LINE_LENGTH,
    MAX_CUSTOMER_CITY_LENGTH,
    MAX_CUSTOMER_NAME_LENGTH,
    MAX_CUSTOMER_PHONE_LENGTH,
    Customer,
    StoreListing,
)

PORTAL_CUSTOMER_COUNTRY_CHOICES = list(
    CUSTOMER_COUNTRY_LABELS.items()
)


class CustomerProfileForm(forms.Form):
    name = forms.CharField(
        max_length=MAX_CUSTOMER_NAME_LENGTH,
        label=gettext_lazy("Store name"),
        error_messages={
            "required": gettext_lazy(
                "Enter the store name."
            ),
            "max_length": gettext_lazy(
                "Store name is too long."
            ),
        },
        widget=forms.TextInput(
            attrs={
                "autocomplete": "organization",
            }
        ),
    )

    # The shop's contact address (order confirmations), not the login:
    # the login stays the invited address, changed by SwedeSweets on
    # request (ops Accounts). Both are the same until the shop changes this.
    email = forms.EmailField(
        max_length=254,
        label=gettext_lazy("Contact email"),
        error_messages={
            "required": gettext_lazy(
                "Enter an email address."
            ),
            "invalid": gettext_lazy(
                "Enter a valid email address."
            ),
            "max_length": gettext_lazy(
                "Email address is too long."
            ),
        },
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
            }
        ),
    )

    phone_number = forms.CharField(
        max_length=MAX_CUSTOMER_PHONE_LENGTH,
        label=gettext_lazy("Phone number"),
        error_messages={
            "required": gettext_lazy(
                "Enter a phone number."
            ),
            "max_length": gettext_lazy(
                "Phone number is too long."
            ),
        },
        widget=forms.TextInput(
            attrs={
                "autocomplete": "tel",
            }
        ),
    )

    country = forms.ChoiceField(
        choices=PORTAL_CUSTOMER_COUNTRY_CHOICES,
        label=gettext_lazy("Country"),
        error_messages={
            "required": gettext_lazy(
                "Choose a country."
            ),
            "invalid_choice": gettext_lazy(
                "Choose a valid country."
            ),
        },
        widget=forms.Select(
            attrs={
                "autocomplete": "country",
                "data-enhanced-select": "true",
                "data-enhanced-select-search": "false",
            }
        ),
    )

    city = forms.CharField(
        max_length=MAX_CUSTOMER_CITY_LENGTH,
        label=gettext_lazy("City"),
        error_messages={
            "required": gettext_lazy(
                "Enter a city."
            ),
            "max_length": gettext_lazy(
                "City is too long."
            ),
        },
        widget=forms.TextInput(
            attrs={
                "autocomplete": "address-level2",
            }
        ),
    )

    address_line = forms.CharField(
        max_length=MAX_CUSTOMER_ADDRESS_LINE_LENGTH,
        label=gettext_lazy("Delivery address"),
        error_messages={
            "required": gettext_lazy(
                "Enter a street address."
            ),
            "max_length": gettext_lazy(
                "Address is too long."
            ),
        },
        widget=forms.TextInput(
            attrs={
                "autocomplete": "street-address",
            }
        ),
    )

    # Find Sweets: the public list of shops that sell SwedeSweets.
    # Same chips as Active/Inactive elsewhere; left out of a post, the
    # store is not listed.
    is_listed = forms.TypedChoiceField(
        required=False,
        choices=(
            ("true", gettext_lazy("Listed")),
            ("false", gettext_lazy("Not listed")),
        ),
        coerce=lambda value: value == "true",
        empty_value=False,
        initial="false",
        label=gettext_lazy("Status"),
        help_text=gettext_lazy(
            "Let visitors find your store on the public list of shops that "
            "sell SwedeSweets."
        ),
        widget=forms.RadioSelect(attrs={"class": "radio-chip-group"}),
    )

    store_address_line = forms.CharField(
        required=False,
        max_length=MAX_CUSTOMER_ADDRESS_LINE_LENGTH,
        label=gettext_lazy("Store address"),
        help_text=gettext_lazy(
            "Only if visitors find you somewhere else than the delivery "
            "address."
        ),
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
            }
        ),
    )

    store_city = forms.CharField(
        required=False,
        max_length=MAX_CUSTOMER_CITY_LENGTH,
        label=gettext_lazy("Store city"),
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
            }
        ),
    )

    DELIVERY_FIELDS = (
        "name",
        "email",
        "phone_number",
        "country",
        "city",
        "address_line",
    )
    LISTING_FIELDS = (
        "is_listed",
        "store_address_line",
        "store_city",
    )

    def clean(self):
        cleaned = super().clean()
        line = (cleaned.get("store_address_line") or "").strip()
        city = (cleaned.get("store_city") or "").strip()

        if line and not city:
            self.add_error(
                "store_city",
                gettext_lazy("Add the store's city too."),
            )
        elif city and not line:
            self.add_error(
                "store_address_line",
                gettext_lazy("Add the store's street address too."),
            )

        return cleaned

    @property
    def delivery_fields(self):
        return [self[name] for name in self.DELIVERY_FIELDS]

    @property
    def listing_fields(self):
        return [self[name] for name in self.LISTING_FIELDS]

    def __init__(
        self,
        *args,
        customer: Customer,
        login_email: str = "",
        **kwargs,
    ) -> None:
        self.customer = customer
        super().__init__(*args, **kwargs)

        if login_email:
            self.fields["email"].help_text = contact_email_help(login_email)

        set_form_field_layout(
            self,
            full=(
                "name",
                "address_line",
                "is_listed",
            ),
            half=(
                "email",
                "phone_number",
                "country",
                "city",
                "store_address_line",
                "store_city",
            ),
        )


def contact_email_help(login_email: str) -> str:
    """Says the field is not the login, which address is, and who changes
    it (us, on request)."""

    contact_link = format_html(
        '<a href="mailto:{}">{}</a>',
        CONTACT_EMAIL,
        gettext("contact us"),
    )

    return format_html(
        gettext(
            "Order confirmations go here. You log in with {login}; to "
            "change that, {contact_link}."
        ),
        login=login_email,
        contact_link=contact_link,
    )


def build_customer_profile_initial_data(
    customer: Customer,
) -> dict[str, object]:
    return {
        "name": customer.name,
        "email": customer.email,
        "phone_number": customer.phone_number,
        "country": customer.country,
        "city": customer.city,
        "address_line": customer.address_line,
        **_store_listing_initial_data(customer),
    }


def _store_listing_initial_data(customer: Customer) -> dict[str, object]:
    listing = StoreListing.objects.filter(customer=customer).first()

    if listing is None:
        return {"is_listed": "false", "store_address_line": "", "store_city": ""}

    return {
        "is_listed": "true" if listing.is_listed else "false",
        "store_address_line": listing.address_line,
        "store_city": listing.city,
    }
