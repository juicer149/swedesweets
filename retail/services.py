from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from carts.models import Cart, CartLine
from carts.services import (
    InvalidCart,
    add_cart_line,
)
from common.channels import SalesChannel
from inventory.errors import InsufficientStockError
from inventory.models import InventoryBatch
from orders.datatypes import BuyerInput
from orders.models import Order, OrderLine
from orders.services import place_order as place_shared_order
from payments.models import PaymentAttempt
from payments.services import (
    InvalidPaymentAttempt,
    create_payment_attempt,
    mark_payment_attempt_failed,
    mark_payment_attempt_succeeded,
)
from pricing.models import CommercialPrice, PriceAmount
from products.models import Product
from reservations.planning import InsufficientReservationCapacity
from reservations.policies import (
    make_order_reservations_permanent_before_placement,
)
from reservations.services import (
    cancel_temporary_reservations_for_order,
    reserve_order_line_from_pool,
)
from retail.models import RetailCheckoutSession
from retail.rules import (
    MAX_RETAIL_LINE_QUANTITY,
    MAX_RETAIL_ORDER_LINES,
    MAX_RETAIL_ORDER_TOTAL,
    MIN_RETAIL_LINE_QUANTITY,
    RETAIL_CHECKOUT_WINDOW,
    RETAIL_PAYMENT_RESERVATION_WINDOW,
    is_supported_retail_destination,
)
from retail.selectors import list_batches_for_retail_price


class InvalidRetailCart(ValueError):
    """Raised when a retail cart use case violates a retail invariant."""


@transaction.atomic
def add_retail_cart_line(
    *,
    cart: Cart,
    commercial_price_id: int,
    quantity: int,
) -> CartLine:
    """Resolve an eligible RETAIL offer and add it to a cart."""

    commercial_price, _ = _get_retail_price_and_amount(
        commercial_price_id=commercial_price_id,
        currency=PriceAmount.Currency.EUR,
    )

    try:
        return add_cart_line(
            cart=cart,
            commercial_price=commercial_price,
            quantity=quantity,
        )
    except InvalidCart as exc:
        raise InvalidRetailCart(
            str(exc)
        ) from exc


class InvalidRetailOrder(ValueError):
    """Raised when a retail checkout violates a business invariant."""


@dataclass(frozen=True, slots=True)
class AnonymousBuyerInput:
    first_name: str
    last_name: str
    email: str
    phone_number: str
    country: str
    postal_code: str
    city: str
    address_line: str


@dataclass(frozen=True, slots=True)
class RetailOrderLineInput:
    commercial_price_id: int
    quantity: int


@dataclass(frozen=True, slots=True)
class ResolvedRetailOrderLine:
    """Validated retail line with commercial pricing resolved server-side."""

    product: Product
    quantity: int
    unit_price: Decimal
    commercial_price: CommercialPrice

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity


def buyer_from_anonymous_retail_input(
    *,
    buyer: AnonymousBuyerInput,
) -> BuyerInput:
    """Adapt anonymous retail input to the shared buyer contract."""

    first_name = " ".join(
        buyer.first_name.strip().split()
    )
    last_name = " ".join(
        buyer.last_name.strip().split()
    )

    return BuyerInput(
        name=" ".join(
            part
            for part in (
                first_name,
                last_name,
            )
            if part
        ),
        email=buyer.email.strip(),
        phone_number=buyer.phone_number.strip(),
        country=buyer.country.strip().upper(),
        postal_code=buyer.postal_code.strip(),
        city=" ".join(
            buyer.city.strip().split()
        ),
        address_line=" ".join(
            buyer.address_line.strip().split()
        ),
    )


@transaction.atomic
def create_retail_checkout_from_cart(
    *,
    cart: Cart,
    buyer: AnonymousBuyerInput,
) -> RetailCheckoutSession:
    """Convert one mutable retail cart into a validated retail checkout."""

    cart = _lock_retail_cart_for_checkout(
        cart=cart,
    )

    cart_lines = list(
        cart.lines.order_by("id")
    )

    if not cart_lines:
        raise InvalidRetailCart(
            "retail cart is empty"
        )

    checkout = create_pending_retail_order(
        buyer=buyer,
        lines=[
            RetailOrderLineInput(
                commercial_price_id=line.commercial_price_id,
                quantity=line.quantity,
            )
            for line in cart_lines
        ],
    )

    cart.delete()

    return checkout


@transaction.atomic
def create_pending_retail_order(
    *,
    buyer: AnonymousBuyerInput,
    lines: list[RetailOrderLineInput],
) -> RetailCheckoutSession:
    """Create a validated retail checkout without reserving stock."""

    _validate_buyer_destination(
        buyer
    )
    _validate_lines(
        lines
    )

    resolved_lines = _resolve_retail_lines(
        lines=lines,
        currency=PriceAmount.Currency.EUR,
    )
    _validate_unique_commercial_prices(
        lines=resolved_lines,
    )

    total = _calculate_order_total(
        lines=resolved_lines,
    )

    if total > MAX_RETAIL_ORDER_TOTAL:
        raise InvalidRetailOrder(
            "order total exceeds maximum allowed amount"
        )

    order = Order(
        channel=Order.Channel.RETAIL,
        currency=Order.Currency.EUR,
        customer=None,
        status=Order.Status.DRAFT,
    )
    order.snapshot_buyer(
        buyer=buyer_from_anonymous_retail_input(
            buyer=buyer,
        ),
    )
    order.save()

    for resolved_line in resolved_lines:
        OrderLine.objects.create(
            order=order,
            product=resolved_line.product,
            quantity=resolved_line.quantity,
            unit=OrderLine.Unit.STOCK_UNIT,
            quantity_in_units=resolved_line.quantity,
            unit_price_snapshot=resolved_line.unit_price,
            commercial_offer=resolved_line.commercial_price,
        )


    return RetailCheckoutSession.objects.create(
        order=order,
        expires_at=(
            timezone.now()
            + RETAIL_CHECKOUT_WINDOW
        ),
    )


@transaction.atomic
def start_retail_payment(
    *,
    checkout: RetailCheckoutSession,
) -> PaymentAttempt:
    """Prepare one retail order for a new external payment attempt.

    A retail order may have at most one active payment workflow.

    Existing pending payment attempts are never implicitly replaced here.
    Provider initialization for an existing pending attempt must instead be
    retried or reconciled explicitly.

    The checkout and order are locked while retail availability is
    re-evaluated.

    The returned PaymentAttempt exists only after every order line has been
    successfully reserved.

    No payment-provider call happens while these database locks are held.
    """

    now = timezone.now()

    checkout = (
        RetailCheckoutSession.objects
        .select_for_update()
        .get(pk=checkout.pk)
    )

    order = (
        Order.objects
        .select_for_update()
        .get(pk=checkout.order_id)
    )

    if checkout.expires_at <= now:
        raise InvalidRetailOrder(
            "retail checkout has expired"
        )

    if order.channel != Order.Channel.RETAIL:
        raise InvalidRetailOrder(
            "checkout does not belong to a retail order"
        )

    if order.status != Order.Status.DRAFT:
        raise InvalidRetailOrder(
            "only draft retail orders can start payment"
        )

    pending_attempt = (
        PaymentAttempt.objects
        .select_for_update()
        .filter(
            order=order,
            status=PaymentAttempt.Status.PENDING,
        )
        .first()
    )

    if pending_attempt is not None:
        raise InvalidRetailOrder(
            "retail order already has a pending payment attempt"
        )

    lines = list(
        order.lines
        .select_related(
            "product",
            "commercial_offer__product",
            "commercial_offer__batch__product",
        )
        .order_by("id")
    )

    if not lines:
        raise InvalidRetailOrder(
            "retail checkout has no order lines"
        )

    cancel_temporary_reservations_for_order(
        order=order,
    )

    reserved_until = (
        now
        + RETAIL_PAYMENT_RESERVATION_WINDOW
    )

    for line in lines:
        batches = _eligible_batches_for_offer(
            commercial_price=line.commercial_offer,
            currency=order.currency,
        )

        try:
            reserve_order_line_from_pool(
                order_line=line,
                batches=batches,
                quantity=line.quantity_in_units,
                reserved_until=reserved_until,
            )
        except InsufficientReservationCapacity as exc:
            raise InsufficientStockError(
                product_name=line.product.display_name,
                requested_quantity=exc.requested_quantity,
                available_quantity=exc.available_quantity,
                missing_quantity=exc.missing_quantity,
            ) from exc

    return create_payment_attempt(
        order=order,
    )


@transaction.atomic
def complete_retail_payment(
    *,
    attempt: PaymentAttempt,
    provider_transaction_id: str | None = None,
) -> Order:
    """Finalize a successfully paid retail checkout.

    Lock ordering is Order -> PaymentAttempt, matching payment-start paths.
    """

    order_id = (
        PaymentAttempt.objects
        .only("order_id")
        .get(pk=attempt.pk)
        .order_id
    )

    order = (
        Order.objects
        .select_for_update()
        .get(pk=order_id)
    )

    attempt = (
        PaymentAttempt.objects
        .select_for_update()
        .get(pk=attempt.pk)
    )

    if attempt.order_id != order.pk:
        raise InvalidPaymentAttempt(
            "payment attempt order changed unexpectedly"
        )

    if attempt.status != PaymentAttempt.Status.PENDING:
        raise InvalidPaymentAttempt(
            "only pending payment attempts can complete retail payment"
        )

    if order.channel != Order.Channel.RETAIL:
        raise InvalidRetailOrder(
            "payment attempt does not belong to a retail order"
        )

    order = place_shared_order(
        order=order,
        preparation=(
            make_order_reservations_permanent_before_placement
        ),
    )

    mark_payment_attempt_succeeded(
        attempt=attempt,
        provider_transaction_id=provider_transaction_id,
    )

    return order


@transaction.atomic
def fail_retail_payment(
    *,
    attempt: PaymentAttempt,
) -> PaymentAttempt:
    """Finalize a failed retail payment attempt.

    Lock ordering is Order -> PaymentAttempt, matching payment-start paths.
    """

    order_id = (
        PaymentAttempt.objects
        .only("order_id")
        .get(pk=attempt.pk)
        .order_id
    )

    order = (
        Order.objects
        .select_for_update()
        .get(pk=order_id)
    )

    attempt = (
        PaymentAttempt.objects
        .select_for_update()
        .get(pk=attempt.pk)
    )

    if attempt.order_id != order.pk:
        raise InvalidPaymentAttempt(
            "payment attempt order changed unexpectedly"
        )

    if attempt.status != PaymentAttempt.Status.PENDING:
        raise InvalidPaymentAttempt(
            "only pending payment attempts can fail retail payment"
        )

    if order.channel != Order.Channel.RETAIL:
        raise InvalidRetailOrder(
            "payment attempt does not belong to a retail order"
        )

    if order.status != Order.Status.DRAFT:
        raise InvalidRetailOrder(
            "only draft retail orders can fail payment"
        )

    cancel_temporary_reservations_for_order(
        order=order,
    )

    return mark_payment_attempt_failed(
        attempt=attempt,
    )


def _lock_retail_cart_for_checkout(
    *,
    cart: Cart,
) -> Cart:
    try:
        cart = (
            Cart.objects
            .select_for_update()
            .get(pk=cart.pk)
        )
    except Cart.DoesNotExist as exc:
        raise InvalidRetailCart(
            "retail cart does not exist"
        ) from exc

    if cart.channel != SalesChannel.RETAIL:
        raise InvalidRetailCart(
            "cart does not belong to retail"
        )

    return cart


def _eligible_batches_for_offer(
    *,
    commercial_price: CommercialPrice,
    currency: str,
) -> QuerySet[InventoryBatch]:
    return list_batches_for_retail_price(
        commercial_price=commercial_price,
        currency=currency,
    )


def _validate_buyer_destination(
    buyer: AnonymousBuyerInput,
) -> None:
    if not is_supported_retail_destination(
        country_code=buyer.country,
        postal_code=buyer.postal_code,
        city=buyer.city,
    ):
        raise InvalidRetailOrder(
            "unsupported retail destination"
        )


def _validate_lines(
    lines: list[RetailOrderLineInput],
) -> None:
    if not lines:
        raise InvalidRetailOrder(
            "order must contain at least one line"
        )

    if len(lines) > MAX_RETAIL_ORDER_LINES:
        raise InvalidRetailOrder(
            "order contains too many lines"
        )

    for line in lines:
        if not (
            MIN_RETAIL_LINE_QUANTITY
            <= line.quantity
            <= MAX_RETAIL_LINE_QUANTITY
        ):
            raise InvalidRetailOrder(
                "invalid retail line quantity"
            )


def _resolve_retail_lines(
    *,
    lines: list[RetailOrderLineInput],
    currency: str,
) -> list[ResolvedRetailOrderLine]:
    return [
        _resolve_retail_line(
            line=line,
            currency=currency,
        )
        for line in lines
    ]


def _resolve_retail_line(
    *,
    line: RetailOrderLineInput,
    currency: str,
) -> ResolvedRetailOrderLine:
    commercial_price, amount = _get_retail_price_and_amount(
        commercial_price_id=line.commercial_price_id,
        currency=currency,
    )

    if (
        commercial_price.batch_id is not None
        and not list_batches_for_retail_price(
            commercial_price=commercial_price,
            currency=currency,
        ).exists()
    ):
        raise InvalidRetailOrder(
            "batch retail price is not currently sellable"
        )

    return ResolvedRetailOrderLine(
        product=commercial_price.product,
        quantity=line.quantity,
        unit_price=amount.price,
        commercial_price=commercial_price,
    )


def _get_retail_price_and_amount(
    *,
    commercial_price_id: int,
    currency: str,
) -> tuple[CommercialPrice, PriceAmount]:
    try:
        commercial_price = (
            CommercialPrice.objects
            .select_related(
                "product",
                "batch__product",
            )
            .get(pk=commercial_price_id)
        )
    except CommercialPrice.DoesNotExist as exc:
        raise InvalidRetailOrder(
            "retail commercial price does not exist"
        ) from exc

    if commercial_price.channel != CommercialPrice.Channel.RETAIL:
        raise InvalidRetailOrder(
            "commercial price does not belong to retail"
        )

    if not commercial_price.enabled:
        raise InvalidRetailOrder(
            "commercial price is not enabled for retail"
        )

    if not commercial_price.product.active:
        raise InvalidRetailOrder(
            "product is not enabled for retail"
        )

    try:
        amount = commercial_price.amounts.get(
            currency=currency,
        )
    except PriceAmount.DoesNotExist as exc:
        raise InvalidRetailOrder(
            f"commercial price has no {currency} amount"
        ) from exc

    return commercial_price, amount


def _validate_unique_commercial_prices(
    *,
    lines: list[ResolvedRetailOrderLine],
) -> None:
    price_ids: set[int] = set()

    for line in lines:
        if line.commercial_price.pk in price_ids:
            raise InvalidRetailOrder(
                "duplicate retail commercial price lines are not allowed"
            )

        price_ids.add(
            line.commercial_price.pk,
        )


def _calculate_order_total(
    *,
    lines: list[ResolvedRetailOrderLine],
) -> Decimal:
    return sum(
        (
            line.line_total
            for line in lines
        ),
        start=Decimal("0.00"),
    )
