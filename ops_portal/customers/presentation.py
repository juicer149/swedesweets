"""How a customer reads on the ops pages (list rows, detail heading)."""

from __future__ import annotations

from customers.models import Customer


def customer_status_key(customer: Customer) -> str:
    return "active" if customer.is_active else "inactive"


def customer_status_label(customer: Customer) -> str:
    return "Active" if customer.is_active else "Inactive"


def customer_status_icon(customer: Customer) -> str:
    return "users" if customer.is_active else "x"


def customer_place_label(customer: Customer) -> str:
    """Chamonix-Mont-Blanc, France"""

    return ", ".join(part for part in (customer.city, customer.country_name) if part)
