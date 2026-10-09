from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

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

CUSTOMER_COUNTRY_CHOICES = list(CUSTOMER_COUNTRY_LABELS.items())


class CustomerForm(forms.Form):
    name = forms.CharField(
        max_length=MAX_CUSTOMER_NAME_LENGTH,
        label="Customer name",
        error_messages={
            "required": "Enter the customer name.",
            "max_length": (
                f"Customer name must be at most {MAX_CUSTOMER_NAME_LENGTH} characters."
            ),
        },
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. Nordic Corner Shop",
                "autocomplete": "name",
            }
        ),
    )

    email = forms.EmailField(
        max_length=254,
        label="Contact email",
        help_text=(
            "Where order confirmations go. Logins are separate, under "
            "Accounts."
        ),
        error_messages={
            "required": "Enter an email address.",
            "invalid": "Enter a valid email address.",
            "max_length": "Email address must be at most 254 characters.",
        },
        widget=forms.EmailInput(
            attrs={
                "placeholder": "e.g. orders@example.fr",
                "autocomplete": "email",
            }
        ),
    )

    phone_number = forms.CharField(
        max_length=MAX_CUSTOMER_PHONE_LENGTH,
        label="Phone number",
        error_messages={
            "required": "Enter a phone number.",
            "max_length": (
                f"Phone number must be at most {MAX_CUSTOMER_PHONE_LENGTH} characters."
            ),
        },
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. +33 6 12 34 56 78",
                "autocomplete": "tel",
            }
        ),
    )

    country = forms.ChoiceField(
        choices=CUSTOMER_COUNTRY_CHOICES,
        label="Country",
        initial="FR",
        error_messages={
            "required": "Choose a country.",
            "invalid_choice": "Choose a valid country.",
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
        label="City",
        initial="Chamonix-Mont-Blanc",
        error_messages={
            "required": "Enter a city.",
            "max_length": (
                f"City must be at most {MAX_CUSTOMER_CITY_LENGTH} characters."
            ),
        },
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. Chamonix-Mont-Blanc",
                "autocomplete": "address-level2",
            }
        ),
    )

    address_line = forms.CharField(
        max_length=MAX_CUSTOMER_ADDRESS_LINE_LENGTH,
        label="Address",
        error_messages={
            "required": "Enter a street address.",
            "max_length": (
                f"Address must be at most "
                f"{MAX_CUSTOMER_ADDRESS_LINE_LENGTH} characters."
            ),
        },
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. 123 Rue du Mont Blanc",
                "autocomplete": "street-address",
            }
        ),
    )

    # Find Sweets: the public list of shops. Only when editing; a new
    # customer starts unlisted and the shop can opt in from its portal.
    is_listed = forms.TypedChoiceField(
        choices=(("true", "Listed"), ("false", "Not listed")),
        coerce=lambda value: value == "true",
        initial="false",
        label="Status",
        help_text="Listed shops appear on the public Find Sweets page.",
        error_messages={
            "required": "Choose whether the shop is listed.",
            "invalid_choice": "Choose a valid listing status.",
        },
        widget=forms.RadioSelect(attrs={"class": "radio-chip-group"}),
    )

    store_address_line = forms.CharField(
        required=False,
        max_length=MAX_CUSTOMER_ADDRESS_LINE_LENGTH,
        label="Store address",
        help_text=(
            "Only if visitors find the shop somewhere else than the "
            "delivery address."
        ),
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )

    store_city = forms.CharField(
        required=False,
        max_length=MAX_CUSTOMER_CITY_LENGTH,
        label="Store city",
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
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

    def __init__(self, *args, customer: Customer | None = None, **kwargs) -> None:
        self.customer = customer
        super().__init__(*args, **kwargs)

        if customer is None:
            for name in self.LISTING_FIELDS:
                del self.fields[name]

        set_form_field_layout(
            self,
            full=("name", "address_line"),
            half=("email", "phone_number", "country", "city"),
        )

        if customer is not None:
            set_form_field_layout(
                self,
                full=("is_listed",),
                half=("store_address_line", "store_city"),
            )

    def clean(self):
        cleaned = super().clean()

        if self.customer is None:
            return cleaned

        line = (cleaned.get("store_address_line") or "").strip()
        city = (cleaned.get("store_city") or "").strip()

        if line and not city:
            self.add_error("store_city", "Add the store's city too.")
        elif city and not line:
            self.add_error("store_address_line", "Add the store's street address too.")

        return cleaned

    @property
    def delivery_fields(self):
        return [self[name] for name in self.DELIVERY_FIELDS]

    @property
    def listing_fields(self):
        return [self[name] for name in self.LISTING_FIELDS if name in self.fields]

    @property
    def delivery_data(self) -> dict[str, object]:
        return {name: self.cleaned_data[name] for name in self.DELIVERY_FIELDS}


def build_customer_edit_initial_data(customer: Customer) -> dict[str, object]:
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


def email_taken_message(email: str, *, check_customers: bool) -> str | None:
    """Why this email cannot get an invitation, or None when it is free.

    Checked before anything is created, so the answer shows on the email
    field itself (the services refuse the same, as a last guard)."""

    if check_customers:
        customer = Customer.objects.filter(email__iexact=email).first()

        if customer is not None:
            return (
                f"{customer.name} already uses this email. To give them a "
                "login, open the customer and choose Invite to the portal."
            )

    user = (
        get_user_model().objects
        .filter(Q(email__iexact=email) | Q(username__iexact=email))
        .select_related("customer_membership__customer")
        .first()
    )

    if user is None:
        return None

    membership = getattr(user, "customer_membership", None)

    if membership is not None:
        return f"This email already has a login, for {membership.customer.name}."

    return "This email already has a login."


class InviteShopForm(CustomerForm):
    """A new shop and its login in one go: name, email and country only.
    The shop fills in phone, city and address itself on first login."""

    DELIVERY_FIELDS = ("name", "email", "country")
    LEFT_TO_THE_SHOP = ("phone_number", "city", "address_line")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, customer=None, **kwargs)

        for name in self.LEFT_TO_THE_SHOP:
            del self.fields[name]

        # One address for both at the start: the login, and where order
        # confirmations go. The shop can change the contact one later.
        self.fields["email"].label = "Email"
        self.fields["email"].help_text = "Their login, and where the invitation goes."

    def clean_email(self) -> str:
        email = self.cleaned_data["email"].strip().lower()
        taken = email_taken_message(email, check_customers=True)

        if taken:
            raise forms.ValidationError(taken)

        return email

    @property
    def delivery_data(self) -> dict[str, object]:
        return {
            **{name: self.cleaned_data[name] for name in self.DELIVERY_FIELDS},
            **{name: "" for name in self.LEFT_TO_THE_SHOP},
        }


class InviteLoginForm(forms.Form):
    """A login for a customer that exists already (or a second person)."""

    email = forms.EmailField(
        max_length=254,
        label="Login email",
        help_text=(
            "We email an invitation here, with a link to choose a password."
        ),
        error_messages={
            "required": "Enter an email address.",
            "invalid": "Enter a valid email address.",
        },
        widget=forms.EmailInput(
            attrs={
                "placeholder": "e.g. orders@example.fr",
                "autocomplete": "email",
            }
        ),
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        set_form_field_layout(self, full=("email",))

    def clean_email(self) -> str:
        email = self.cleaned_data["email"].strip().lower()
        # The customer's own email is the usual choice here, so only an
        # existing login stops it.
        taken = email_taken_message(email, check_customers=False)

        if taken:
            raise forms.ValidationError(taken)

        return email

    @property
    def delivery_fields(self):
        return [self["email"]]

    @property
    def listing_fields(self):
        return []
