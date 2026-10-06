"""
Customer application services.

These functions coordinate customer use-cases. Customer data belongs to the
customers domain. Orders may reference customers, but should not own customer
creation or customer validation rules.
"""

from __future__ import annotations

from django.db import IntegrityError, transaction

from customers.errors import InvalidCustomerData
from customers.models import Customer, normalize_customer_email

CUSTOMER_EMAIL_EXISTS_MESSAGE = "Customer with email {email} already exists"


def _ensure_customer_email_is_available(
    *,
    email: str,
    exclude_customer: Customer | None = None,
) -> None:
    customers = Customer.objects.filter(email=email)

    if exclude_customer is not None:
        customers = customers.exclude(pk=exclude_customer.pk)

    if customers.exists():
        raise InvalidCustomerData(CUSTOMER_EMAIL_EXISTS_MESSAGE.format(email=email))


@transaction.atomic
def create_customer(
    *,
    name: str,
    email: str,
    phone_number: str,
    country: str,
    city: str,
    address_line: str,
    user=None,
) -> Customer:
    """Create a customer with unique normalized email."""

    normalized_email = normalize_customer_email(email)
    _ensure_customer_email_is_available(email=normalized_email)

    try:
        customer = Customer.objects.create(
            name=name,
            email=normalized_email,
            phone_number=phone_number,
            country=country,
            city=city,
            address_line=address_line,
        )
    except IntegrityError as exc:
        raise InvalidCustomerData(
            CUSTOMER_EMAIL_EXISTS_MESSAGE.format(email=normalized_email)
        ) from exc

    customer.mark_as_created(user=user)

    return customer


@transaction.atomic
def update_customer(
    *,
    customer: Customer,
    name: str,
    email: str,
    phone_number: str,
    country: str,
    city: str,
    address_line: str,
    user=None,
) -> Customer:
    """Update editable customer contact and delivery data."""

    customer = Customer.objects.select_for_update().get(pk=customer.pk)
    normalized_email = normalize_customer_email(email)

    _ensure_customer_email_is_available(
        email=normalized_email,
        exclude_customer=customer,
    )

    customer.name = name
    customer.email = normalized_email
    customer.phone_number = phone_number
    customer.country = country
    customer.city = city
    customer.address_line = address_line

    try:
        customer.save(
            update_fields=[
                "name",
                "email",
                "phone_number",
                "country",
                "city",
                "address_line",
            ]
        )
    except IntegrityError as exc:
        raise InvalidCustomerData(
            CUSTOMER_EMAIL_EXISTS_MESSAGE.format(email=normalized_email)
        ) from exc

    customer.mark_as_edited(user=user)

    return customer


@transaction.atomic
def update_customer_listing(
    *,
    customer: Customer,
    listed_publicly: bool,
    store_address_line: str = "",
    store_city: str = "",
    user=None,
) -> Customer:
    """Whether the shop is on Find Sweets, and its own street address.

    The store address is both line and city or neither; without it Find
    Sweets shows the delivery address.
    """

    store_address_line = (store_address_line or "").strip()
    store_city = (store_city or "").strip()

    if bool(store_address_line) != bool(store_city):
        raise InvalidCustomerData(
            "Give both the store's street address and its city, or neither."
        )

    customer = Customer.objects.select_for_update().get(pk=customer.pk)
    customer.listed_publicly = listed_publicly
    customer.store_address_line = store_address_line
    customer.store_city = store_city
    customer.save(
        update_fields=[
            "listed_publicly",
            "store_address_line",
            "store_city",
        ]
    )
    customer.mark_as_edited(user=user)

    return customer


@transaction.atomic
def deactivate_customer(
    *,
    customer: Customer,
    user=None,
) -> Customer:
    customer = Customer.objects.select_for_update().get(pk=customer.pk)
    customer.deactivate(user=user)

    return customer


@transaction.atomic
def reactivate_customer(
    *,
    customer: Customer,
    user=None,
) -> Customer:
    customer = Customer.objects.select_for_update().get(pk=customer.pk)
    customer.reactivate(user=user)

    return customer
