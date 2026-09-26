from __future__ import annotations

from django.db import transaction

from business.models import BusinessCart
from carts.models import Cart, CartLine
from carts.services import (
    InvalidCart,
    add_cart_line,
    create_cart,
)
from common.channels import SalesChannel
from customers.models import Customer
from pricing.models import (
    CommercialPrice,
    PriceAmount,
)
from products.models import Product


class InvalidBusinessCart(ValueError):
    """Raised when a business cart use case violates a business invariant."""


@transaction.atomic
def get_or_create_customer_cart(
    *,
    customer: Customer,
) -> Cart:
    """Return the customer's active BUSINESS cart, creating one if needed."""

    business_cart = (
        BusinessCart.objects
        .select_related(
            "cart",
        )
        .filter(
            customer_id=customer.pk,
        )
        .first()
    )

    if business_cart is not None:
        return _require_business_cart(
            cart=business_cart.cart,
        )

    # Serialize creation per customer. Without this lock, two concurrent
    # requests could both observe that no BusinessCart exists yet.
    customer = (
        Customer.objects
        .select_for_update()
        .get(pk=customer.pk)
    )

    # Another transaction may have created the association before this
    # transaction acquired the customer lock.
    business_cart = (
        BusinessCart.objects
        .select_related(
            "cart",
        )
        .filter(
            customer_id=customer.pk,
        )
        .first()
    )

    if business_cart is not None:
        return _require_business_cart(
            cart=business_cart.cart,
        )

    cart = create_cart(
        channel=SalesChannel.BUSINESS,
    )

    BusinessCart.objects.create(
        cart=cart,
        customer=customer,
    )

    return cart


@transaction.atomic
def add_catalog_offer_to_cart(
    *,
    customer: Customer,
    product: Product,
    commercial_price_id: int | None,
    quantity: int = 1,
) -> CartLine:
    """Add one commercially eligible BUSINESS offer to a customer's cart.

    Product is route/catalog scope only. The durable commercial selection
    stored on CartLine is the resolved CommercialPrice.

    Current stock and order limits deliberately do not constrain mutable
    cart intent. They are revalidated when the cart becomes an Order.
    """

    commercial_price = _get_business_cart_offer(
        product=product,
        commercial_price_id=commercial_price_id,
    )

    cart = get_or_create_customer_cart(
        customer=customer,
    )

    try:
        return add_cart_line(
            cart=cart,
            commercial_price=commercial_price,
            quantity=quantity,
        )
    except InvalidCart as exc:
        raise InvalidBusinessCart(
            str(exc)
        ) from exc


def _get_business_cart_offer(
    *,
    product: Product,
    commercial_price_id: int | None,
) -> CommercialPrice:
    if not product.active:
        raise InvalidBusinessCart(
            "business offer is not currently available"
        )

    queryset = (
        CommercialPrice.objects
        .select_related(
            "product",
        )
        .prefetch_related(
            "amounts",
        )
    )

    if commercial_price_id is None:
        commercial_price = (
            queryset
            .filter(
                product_id=product.pk,
                channel=CommercialPrice.Channel.BUSINESS,
                batch__isnull=True,
            )
            .first()
        )

        if commercial_price is None:
            raise RuntimeError(
                "business ordering invariant violated: "
                "missing standard BUSINESS offer for "
                f"{product.display_name}"
            )
    else:
        commercial_price = (
            queryset
            .filter(
                pk=commercial_price_id,
            )
            .first()
        )

        if commercial_price is None:
            raise InvalidBusinessCart(
                "business offer is not currently available"
            )

    if (
        commercial_price.product_id != product.pk
        or commercial_price.channel
        != CommercialPrice.Channel.BUSINESS
        or not commercial_price.enabled
        or not commercial_price.product.active
    ):
        raise InvalidBusinessCart(
            "business offer is not currently available"
        )

    if (
        commercial_price.batch_id is not None
        and not any(
            amount.currency == PriceAmount.Currency.EUR
            for amount in commercial_price.amounts.all()
        )
    ):
        raise InvalidBusinessCart(
            "business offer is not currently available"
        )

    return commercial_price


def _require_business_cart(
    *,
    cart: Cart,
) -> Cart:
    if cart.channel != SalesChannel.BUSINESS:
        raise RuntimeError(
            "business cart invariant violated: "
            "cart does not belong to business channel"
        )

    return cart
