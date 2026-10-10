from __future__ import annotations

from collections.abc import Iterable

from django.db import transaction

from business.datatypes import BusinessOfferLineInput
from business.drafts import (
    build_business_offer_order_draft,
    build_business_order_draft,
    resolve_business_order_lines,
)
from business.policies import (
    prepare_business_order_for_placement,
)
from carts.models import Cart
from carts.services import (
    InvalidCart,
)
from carts.services import (
    clear_cart as clear_generic_cart,
)
from common.channels import SalesChannel
from customers.models import Customer
from orders.datatypes import OrderLineInput
from orders.errors import InvalidOrderOperation
from orders.models import Order
from orders.notifications import (
    send_order_placed_mails_on_commit,
)
from orders.services import (
    create_draft_order as create_shared_draft_order,
)
from orders.services import (
    discard_draft_order as discard_shared_draft_order,
)
from orders.services import (
    place_order as place_shared_order,
)
from orders.services import (
    update_placed_order as update_shared_placed_order,
)
from reservations.policies import (
    clear_order_reservations_before_line_replacement,
    require_order_without_reservations_before_discard,
)


@transaction.atomic
def create_draft_order(
    *,
    customer: Customer,
    lines: Iterable[OrderLineInput],
) -> Order:
    """Create an ordinary unpriced business order in DRAFT status."""

    draft = build_business_order_draft(
        customer=customer,
        lines=lines,
    )

    return create_shared_draft_order(
        draft=draft,
    )


@transaction.atomic
def create_order(
    *,
    customer: Customer,
    lines: Iterable[OrderLineInput],
    user=None,
) -> Order:
    """Create and immediately place an ordinary business order."""

    order = create_draft_order(
        customer=customer,
        lines=lines,
    )

    return place_order(
        order=order,
        user=user,
    )


@transaction.atomic
def place_customer_cart(
    *,
    customer: Customer,
    user=None,
) -> Order:
    """Convert the customer's BUSINESS cart into a placed order.

    The cart row serializes placement against concurrent cart mutations.
    The cart is cleared only after successful placement.
    """

    cart = (
        Cart.objects
        .select_for_update()
        .filter(
            business_context__customer_id=customer.pk,
        )
        .first()
    )

    if cart is None:
        raise InvalidOrderOperation(
            "cart must contain at least one line"
        )

    if cart.channel != SalesChannel.BUSINESS:
        raise RuntimeError(
            "business cart invariant violated: "
            "cart does not belong to business channel"
        )

    cart_lines = tuple(
        cart.lines
        .order_by("id")
        .values_list(
            "commercial_price_id",
            "quantity",
        )
    )

    if not cart_lines:
        raise InvalidOrderOperation(
            "cart must contain at least one line"
        )

    draft = build_business_offer_order_draft(
        customer=customer,
        lines=(
            BusinessOfferLineInput(
                commercial_offer_id=commercial_price_id,
                quantity=quantity,
            )
            for commercial_price_id, quantity in cart_lines
        ),
    )

    order = create_shared_draft_order(
        draft=draft,
    )

    order = place_shared_order(
        order=order,
        preparation=prepare_business_order_for_placement,
        user=user,
    )

    try:
        clear_generic_cart(
            cart=cart,
        )
    except InvalidCart as exc:
        raise RuntimeError(
            "business cart invariant violated: "
            "cart disappeared during placement"
        ) from exc

    send_order_placed_mails_on_commit(order)

    return order


def discard_draft_order(
    *,
    order: Order,
) -> None:
    """Discard a business draft that owns no reservations."""

    discard_shared_draft_order(
        order=order,
        preparation=(
            require_order_without_reservations_before_discard
        ),
    )


def place_order(
    *,
    order: Order,
    user=None,
) -> Order:
    """Place a business draft order."""

    return place_shared_order(
        order=order,
        preparation=prepare_business_order_for_placement,
        user=user,
    )


def update_placed_order(
    *,
    order: Order,
    lines: Iterable[OrderLineInput],
    user=None,
) -> Order:
    """Update ordinary lines and rebuild the business reservation.

    Offer-aware placed-order editing requires a separate explicit use-case;
    this legacy API must not silently reinterpret commercial selections.
    """

    resolved_lines = resolve_business_order_lines(
        lines=lines,
    )

    return update_shared_placed_order(
        order=order,
        lines=resolved_lines,
        before_replacement=(
            clear_order_reservations_before_line_replacement
        ),
        preparation=prepare_business_order_for_placement,
        user=user,
    )
