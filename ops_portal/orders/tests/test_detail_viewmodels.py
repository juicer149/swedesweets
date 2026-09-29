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
from ops_portal.orders.access import can_edit_order
from ops_portal.orders.detail_viewmodels import build_order_secondary_actions


class _AllowAll:
    def allows(self, capability) -> bool:
        return True


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


def test_placed_retail_order_cannot_be_edited_but_can_be_cancelled():
    order = Order(
        pk=7,
        channel=Order.Channel.RETAIL,
        status=Order.Status.PLACED,
        customer=None,
    )

    assert not can_edit_order(order=order, role_spec=_AllowAll())

    labels = [
        action.label
        for action in build_order_secondary_actions(
            order=order,
            role_spec=_AllowAll(),
        )
    ]

    assert labels == ["Cancel order"]


def test_placed_business_order_offers_edit_not_cancel_on_detail():
    order = Order(
        pk=8,
        channel=Order.Channel.BUSINESS,
        status=Order.Status.PLACED,
        customer=Customer(pk=42),
    )

    labels = [
        action.label
        for action in build_order_secondary_actions(
            order=order,
            role_spec=_AllowAll(),
        )
    ]

    assert labels == ["Edit order"]
