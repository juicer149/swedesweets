from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from decimal import Decimal

from business.datatypes import BusinessOfferLineInput
from customers.models import Customer
from orders.datatypes import (
    BuyerInput,
    OrderLineInput,
)
from orders.drafts import (
    OrderDraft,
    ResolvedOrderLine,
)
from orders.errors import InvalidOrderOperation
from orders.models import Order
from orders.order_limits import (
    MAX_QUANTITY_PER_PRODUCT_PER_ORDER,
    is_unusually_large_order_line,
)
from pricing.models import (
    CommercialPrice,
    PriceAmount,
)
from products.models import Product


def buyer_from_customer(
    *,
    customer: Customer,
) -> BuyerInput:
    """Adapt a persisted business customer to the shared buyer contract."""

    return BuyerInput(
        name=customer.name,
        email=customer.email,
        phone_number=customer.phone_number,
        country=customer.country,
        city=customer.city,
        address_line=customer.address_line,
        postal_code="",
    )


def resolve_standard_business_offer(
    *,
    product: Product,
) -> CommercialPrice:
    """Return the product's persistent standard BUSINESS offer.

    A missing or disabled standard offer means the product is not sold in the
    business channel at the standard price (it may be retail-only); ordering
    it is rejected as an invalid order, not treated as a server error.
    """

    offer = (
        CommercialPrice.objects
        .filter(
            product=product,
            channel=CommercialPrice.Channel.BUSINESS,
            batch__isnull=True,
        )
        .first()
    )

    if offer is None or not offer.enabled:
        raise InvalidOrderOperation(
            "product is not available for business ordering"
        )

    return offer


def build_business_order_draft(
    *,
    customer: Customer,
    lines: Iterable[OrderLineInput],
) -> OrderDraft:
    """Resolve business input into a channel-agnostic order draft."""

    resolved_lines = resolve_business_order_lines(
        lines=lines,
    )

    if not resolved_lines:
        raise InvalidOrderOperation(
            "order must contain at least one line"
        )

    return OrderDraft(
        channel=Order.Channel.BUSINESS,
        currency=Order.Currency.EUR,
        customer=customer,
        buyer=buyer_from_customer(
            customer=customer,
        ),
        lines=resolved_lines,
    )


def build_business_offer_order_draft(
    *,
    customer: Customer,
    lines: Iterable[BusinessOfferLineInput],
) -> OrderDraft:
    """Resolve explicit BUSINESS offer selections into a durable order draft."""

    resolved_lines = resolve_business_offer_lines(
        lines=lines,
    )

    if not resolved_lines:
        raise InvalidOrderOperation(
            "order must contain at least one line"
        )

    _validate_business_order_quantity_limits(
        lines=resolved_lines,
    )

    return OrderDraft(
        channel=Order.Channel.BUSINESS,
        currency=Order.Currency.EUR,
        customer=customer,
        buyer=buyer_from_customer(
            customer=customer,
        ),
        lines=resolved_lines,
    )


def _validate_business_order_quantity_limits(
    *,
    lines: Iterable[ResolvedOrderLine],
) -> None:
    quantity_by_product_id: dict[int, int] = defaultdict(int)

    for line in lines:
        quantity_by_product_id[
            line.product.pk
        ] += line.quantity_in_units

    if any(
        is_unusually_large_order_line(
            quantity=quantity,
        )
        for quantity in quantity_by_product_id.values()
    ):
        raise InvalidOrderOperation(
            "maximum quantity per product is "
            f"{MAX_QUANTITY_PER_PRODUCT_PER_ORDER}"
        )


def resolve_business_offer_lines(
    *,
    lines: Iterable[BusinessOfferLineInput],
) -> tuple[ResolvedOrderLine, ...]:
    """Resolve explicit BUSINESS offer selections into order lines.

    Product identity is derived from the selected CommercialPrice rather than
    supplied independently by the caller.

    Duplicate selections of the same offer are merged. Different offers
    for the same product remain distinct lines.
    """

    line_inputs = tuple(lines)

    if not line_inputs:
        return ()

    offer_ids = {
        line_input.commercial_offer_id
        for line_input in line_inputs
    }

    offers_by_id = (
        CommercialPrice.objects
        .select_related(
            "product",
        )
        .prefetch_related(
            "amounts",
        )
        .in_bulk(
            offer_ids,
        )
    )

    missing_offer_ids = sorted(
        offer_ids - offers_by_id.keys()
    )

    if missing_offer_ids:
        raise InvalidOrderOperation(
            "Business offer does not exist: "
            + ", ".join(
                str(offer_id)
                for offer_id in missing_offer_ids
            )
        )

    price_by_offer_id: dict[
        int,
        Decimal | None,
    ] = {}

    for offer_id, offer in offers_by_id.items():
        if (
            offer.channel
            != CommercialPrice.Channel.BUSINESS
        ):
            raise InvalidOrderOperation(
                "commercial offer does not belong "
                "to the business channel"
            )

        if not offer.product.active or not offer.enabled:
            raise InvalidOrderOperation(
                "selected business offer "
                "is not currently available"
            )

        amount = next(
            (
                candidate
                for candidate in offer.amounts.all()
                if (
                    candidate.currency
                    == PriceAmount.Currency.EUR
                )
            ),
            None,
        )

        if (
            offer.batch_id is not None
            and amount is None
        ):
            raise InvalidOrderOperation(
                "business batch offer requires an EUR price"
            )

        price_by_offer_id[offer_id] = (
            amount.price
            if amount is not None
            else None
        )

    quantity_by_offer_id: dict[int, int] = defaultdict(int)

    for line_input in line_inputs:
        offer = offers_by_id[
            line_input.commercial_offer_id
        ]

        quantity_in_units = line_input.quantity

        if quantity_in_units <= 0:
            raise InvalidOrderOperation(
                "order line quantity must be positive"
            )

        quantity_by_offer_id[
            offer.pk
        ] += quantity_in_units

    return tuple(
        ResolvedOrderLine(
            product=offers_by_id[offer_id].product,
            quantity_in_units=quantity,
            commercial_offer=offers_by_id[offer_id],
            unit_price_snapshot=price_by_offer_id[
                offer_id
            ],
        )
        for offer_id, quantity
        in quantity_by_offer_id.items()
    )


def resolve_business_order_lines(
    *,
    lines: Iterable[OrderLineInput],
) -> tuple[ResolvedOrderLine, ...]:
    """Resolve business product lines (quantities in stock units).

    Duplicate product lines are merged.

    Each resolved line carries the product's persistent standard BUSINESS offer
    as its commercial selection. Ordinary product ordering is therefore an
    explicit commercial choice rather than an offer-less special case.
    """

    line_inputs = tuple(lines)

    if not line_inputs:
        return ()

    resolved_inputs = tuple(
        (
            line_input,
            line_input.resolve_product_id(),
        )
        for line_input in line_inputs
    )

    products_by_id = Product.objects.in_bulk(
        product_id
        for _, product_id in resolved_inputs
    )

    quantity_by_product_id: dict[int, int] = defaultdict(int)

    for line_input, product_id in resolved_inputs:
        if product_id not in products_by_id:
            raise InvalidOrderOperation(
                f"Product {product_id} does not exist"
            )

        quantity_in_units = line_input.quantity

        if quantity_in_units <= 0:
            raise InvalidOrderOperation(
                "order line quantity must be positive"
            )

        quantity_by_product_id[
            product_id
        ] += quantity_in_units

    standard_offers_by_product_id = (
        _standard_business_offers_by_product_id(
            products=(
                products_by_id[product_id]
                for product_id in quantity_by_product_id
            ),
        )
    )

    return tuple(
        ResolvedOrderLine(
            product=products_by_id[
                product_id
            ],
            quantity_in_units=quantity,
            commercial_offer=standard_offers_by_product_id[
                product_id
            ],
        )
        for product_id, quantity
        in quantity_by_product_id.items()
    )


def _standard_business_offers_by_product_id(
    *,
    products: Iterable[Product],
) -> dict[int, CommercialPrice]:
    """Resolve standard BUSINESS offers for several products in one query.

    A product without a standard BUSINESS offer, or with a disabled one, is
    not sold in the business channel; asking for it is an invalid order.
    """

    products_by_id = {
        product.id: product
        for product in products
    }

    if not products_by_id:
        return {}

    offers_by_product_id = {
        offer.product_id: offer
        for offer in (
            CommercialPrice.objects
            .filter(
                product_id__in=products_by_id,
                channel=CommercialPrice.Channel.BUSINESS,
                batch__isnull=True,
            )
        )
    }

    unavailable_product_ids = (
        products_by_id.keys() - offers_by_product_id.keys()
    ) | {
        product_id
        for product_id, offer in offers_by_product_id.items()
        if not offer.enabled
    }

    unavailable_product_names = sorted(
        products_by_id[product_id].display_name
        for product_id in unavailable_product_ids
    )

    if unavailable_product_names:
        raise InvalidOrderOperation(
            "product is not available for business ordering: "
            + ", ".join(unavailable_product_names)
        )

    return offers_by_product_id
