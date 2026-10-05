from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.tests.factories import (
    customer_user_factory,
)
from business.services import create_order
from business.tests.factories import (
    standard_business_offer_factory,
)
from customers.tests.factories import (
    customer_factory,
)
from inventory.tests.conftest import TODAY
from inventory.tests.factories import (
    batch_factory,
)
from orders.datatypes import OrderLineInput
from products.tests.factories import (
    product_factory,
)


@pytest.mark.django_db
def test_order_detail_shows_lines_dates_and_actions(
    client,
):
    customer = customer_factory(
        email="detail@example.com",
    )

    client.force_login(
        customer_user_factory(
            customer=customer,
        )
    )

    product = product_factory(
        name="Apple",
        internal_number=301,
    )

    standard_business_offer_factory(
        product=product,
    )

    batch_factory(
        product=product,
        today=TODAY,
        quantity=100,
    )

    order = create_order(
        customer=customer,
        lines=[
            OrderLineInput.units(
                product=product,
                quantity=4,
            ),
        ],
    )

    response = client.get(
        reverse(
            "business_portal:order_detail",
            kwargs={
                "order_id": order.pk,
            },
        )
    )

    assert response.status_code == 200

    (line,) = response.context["content_lines"]

    assert line.quantity == 4
    assert line.image_url is None
    assert response.context["dates"]

    content = response.content.decode()
    repeat_url = reverse(
        "business_portal:repeat_order",
        kwargs={
            "order_id": order.pk,
        },
    )

    assert f'action="{repeat_url}"' in content
    assert f'href="{reverse("business_portal:orders")}"' in content
