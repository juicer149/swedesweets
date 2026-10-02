from __future__ import annotations

import pytest
from django.db import IntegrityError, transaction

from carts.models import Cart
from common.channels import SalesChannel


@pytest.mark.django_db
def test_cart_can_be_created_empty():
    cart = Cart.objects.create(
        channel=SalesChannel.RETAIL,
    )

    assert cart.pk.version == 4
    assert cart.channel == SalesChannel.RETAIL
    assert cart.lines.count() == 0


@pytest.mark.django_db
def test_cart_channel_must_be_valid():
    with pytest.raises(IntegrityError), transaction.atomic():
        Cart.objects.create(
            channel="invalid-channel",
        )
