from __future__ import annotations

from django.db import transaction

from carts.models import Cart, CartLine
from common.channels import SalesChannel
from pricing.models import CommercialPrice


class InvalidCart(ValueError):
    """Raised when a cart mutation violates a cart invariant."""


@transaction.atomic
def create_cart(
    *,
    channel: SalesChannel | str,
) -> Cart:
    """Create an empty mutable cart for one sales channel."""
    try:
        channel = SalesChannel(channel)
    except ValueError as exc:
        raise InvalidCart(
            "invalid sales channel"
        ) from exc

    return Cart.objects.create(
        channel=channel,
    )


@transaction.atomic
def add_cart_line(
    *,
    cart: Cart,
    commercial_price: CommercialPrice,
    quantity: int,
) -> CartLine:
    """Add one commercial selection, merging an existing matching line."""
    _validate_quantity(
        quantity=quantity,
    )

    cart = _lock_cart(
        cart=cart,
    )

    _validate_commercial_price_channel(
        cart=cart,
        commercial_price=commercial_price,
    )

    existing_line = (
        CartLine.objects
        .filter(
            cart=cart,
            commercial_price=commercial_price,
        )
        .first()
    )

    if existing_line is not None:
        existing_line.quantity += quantity
        existing_line.save(
            update_fields=[
                "quantity",
                "updated_at",
            ],
        )
        return existing_line

    return CartLine.objects.create(
        cart=cart,
        commercial_price=commercial_price,
        quantity=quantity,
    )


@transaction.atomic
def update_cart_line_quantity(
    *,
    cart: Cart,
    line: CartLine,
    quantity: int,
) -> CartLine:
    """Set the quantity of one line belonging to the given cart."""
    _validate_quantity(
        quantity=quantity,
    )

    cart = _lock_cart(
        cart=cart,
    )
    line = _get_locked_cart_line(
        cart=cart,
        line=line,
    )

    line.quantity = quantity
    line.save(
        update_fields=[
            "quantity",
            "updated_at",
        ],
    )

    return line


@transaction.atomic
def remove_cart_line(
    *,
    cart: Cart,
    line: CartLine,
) -> None:
    """Remove one line belonging to the given cart."""
    cart = _lock_cart(
        cart=cart,
    )
    line = _get_locked_cart_line(
        cart=cart,
        line=line,
    )

    line.delete()


@transaction.atomic
def clear_cart(
    *,
    cart: Cart,
) -> Cart:
    """Remove every line from a cart."""
    cart = _lock_cart(
        cart=cart,
    )
    cart.lines.all().delete()

    return cart


def _lock_cart(
    *,
    cart: Cart,
) -> Cart:
    try:
        return (
            Cart.objects
            .select_for_update()
            .get(pk=cart.pk)
        )
    except Cart.DoesNotExist as exc:
        raise InvalidCart(
            "cart does not exist"
        ) from exc


def _get_locked_cart_line(
    *,
    cart: Cart,
    line: CartLine,
) -> CartLine:
    try:
        line = (
            CartLine.objects
            .select_for_update()
            .select_related(
                "commercial_price",
            )
            .get(
                pk=line.pk,
                cart=cart,
            )
        )
    except CartLine.DoesNotExist as exc:
        raise InvalidCart(
            "cart line does not belong to cart"
        ) from exc

    _validate_commercial_price_channel(
        cart=cart,
        commercial_price=line.commercial_price,
    )

    return line


def _validate_commercial_price_channel(
    *,
    cart: Cart,
    commercial_price: CommercialPrice,
) -> None:
    if commercial_price.channel != cart.channel:
        raise InvalidCart(
            "commercial price does not belong to cart channel"
        )


def _validate_quantity(
    *,
    quantity: int,
) -> None:
    if quantity <= 0:
        raise InvalidCart(
            "cart line quantity must be positive"
        )
