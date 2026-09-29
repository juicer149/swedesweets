from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _

from common.form_layout import set_form_field_layout
from customers.models import (
    MAX_CUSTOMER_ADDRESS_LINE_LENGTH,
    MAX_CUSTOMER_CITY_LENGTH,
    MAX_CUSTOMER_NAME_LENGTH,
    MAX_CUSTOMER_PHONE_LENGTH,
)
from orders.models import MAX_BUYER_POSTAL_CODE_LENGTH
from retail.delivery_areas import RETAIL_SERVICE_COUNTRY
from retail.rules import is_supported_retail_destination
from retail.services import AnonymousBuyerInput

MAX_NAME_PART_LENGTH = 60


class RetailCheckoutDetailsForm(forms.Form):
    first_name = forms.CharField(
        max_length=MAX_NAME_PART_LENGTH,
        label=_("First name"),
        error_messages={
            "required": _("Enter your first name."),
        },
        widget=forms.TextInput(
            attrs={
                "autocomplete": "given-name",
            }
        ),
    )

    last_name = forms.CharField(
        max_length=MAX_NAME_PART_LENGTH,
        label=_("Last name"),
        error_messages={
            "required": _("Enter your last name."),
        },
        widget=forms.TextInput(
            attrs={
                "autocomplete": "family-name",
            }
        ),
    )

    email = forms.EmailField(
        max_length=254,
        label=_("Email"),
        help_text=_("We send your order confirmation here."),
        error_messages={
            "required": _("Enter your email address."),
            "invalid": _("Enter a valid email address."),
        },
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
            }
        ),
    )

    phone_number = forms.CharField(
        max_length=MAX_CUSTOMER_PHONE_LENGTH,
        label=_("Phone number"),
        help_text=_("Used only if we need to reach you about delivery."),
        error_messages={
            "required": _("Enter your phone number."),
        },
        widget=forms.TextInput(
            attrs={
                "autocomplete": "tel",
                "inputmode": "tel",
                "placeholder": "+33 6 12 34 56 78",
            }
        ),
    )

    address_line = forms.CharField(
        max_length=MAX_CUSTOMER_ADDRESS_LINE_LENGTH,
        label=_("Address"),
        error_messages={
            "required": _("Enter your street address."),
        },
        widget=forms.TextInput(
            attrs={
                "autocomplete": "street-address",
            }
        ),
    )

    postal_code = forms.CharField(
        max_length=MAX_BUYER_POSTAL_CODE_LENGTH,
        label=_("Postal code"),
        error_messages={
            "required": _("Enter your postal code."),
        },
        widget=forms.TextInput(
            attrs={
                "autocomplete": "postal-code",
                "inputmode": "numeric",
            }
        ),
    )

    city = forms.CharField(
        max_length=MAX_CUSTOMER_CITY_LENGTH,
        label=_("City"),
        error_messages={
            "required": _("Enter your city."),
        },
        widget=forms.TextInput(
            attrs={
                "autocomplete": "address-level2",
            }
        ),
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        set_form_field_layout(
            self,
            full=("address_line",),
            half=(
                "first_name",
                "last_name",
                "email",
                "phone_number",
                "postal_code",
                "city",
            ),
        )

    def clean(self) -> dict[str, str]:
        cleaned_data = super().clean()

        first_name = cleaned_data.get("first_name", "").strip()
        last_name = cleaned_data.get("last_name", "").strip()

        if len(f"{first_name} {last_name}") > MAX_CUSTOMER_NAME_LENGTH:
            self.add_error(
                "last_name",
                _("Your full name is too long."),
            )

        postal_code = cleaned_data.get("postal_code")
        city = cleaned_data.get("city")

        if (
            postal_code
            and city
            and not is_supported_retail_destination(
                country_code=RETAIL_SERVICE_COUNTRY,
                postal_code=postal_code,
                city=city,
            )
        ):
            self.add_error(
                "postal_code",
                _(
                    "We don't deliver to this postal code and city yet. "
                    "Check the spelling of the city."
                ),
            )

        return cleaned_data

    def to_buyer_input(self) -> AnonymousBuyerInput:
        data = self.cleaned_data

        return AnonymousBuyerInput(
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            phone_number=data["phone_number"],
            country=RETAIL_SERVICE_COUNTRY,
            postal_code=data["postal_code"],
            city=data["city"],
            address_line=data["address_line"],
        )

    def session_data(self) -> dict[str, str]:
        return {
            name: str(self.cleaned_data[name])
            for name in self.fields
        }
