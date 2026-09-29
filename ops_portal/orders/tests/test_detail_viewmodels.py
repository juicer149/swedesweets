from __future__ import annotations

import pytest

from customers.models import Customer
from ops_portal.orders.detail_viewmodels import (
    CUSTOMER_LABEL,
    RETAIL_BUYER_LABEL,
    buyer_label,
    customer_detail_href,
)
from orders.models import Order


def test_retail_order_without_customer_has_no_customer_link():
    order = Order(
        channel=Order.Channel.RETAIL,
        customer=None,
    )

    assert customer_detail_href(order) is None
    assert buyer_label(order) == RETAIL_BUYER_LABEL


def test_business_order_links_to_its_customer():
    order = Order(
        channel=Order.Channel.BUSINESS,
        customer=Customer(pk=42),
    )

    assert customer_detail_href(order) == "/ops/customers/42/"
    assert buyer_label(order) == CUSTOMER_LABEL
