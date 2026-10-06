from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from business.selectors import (
    list_business_catalog_products,
)
from business_portal.orders.presentation import (
    business_order_status_label,
    contents_summary,
    order_status_icon,
    quantity_label,
)
from business_portal.orders.product_presentation import (
    business_order_line_presentation,
)
from common.lines import META_OFFER, LineView, meta, metas
from orders.models import (
    Order,
    OrderLine,
)
from products.images import product_image_url
from products.models import Product

UNAVAILABLE_LABEL = _("Not currently available in the catalog")


@dataclass(frozen=True, slots=True)
class PortalOrderContentLine:
    product: Product
    quantity: int
    quantity_label: str
    unit: str
    catalog_label: str
    offer_label: str | None
    price_label: str | None
    catalog_href: str | None
    image_url: str | None

    @property
    def view(self) -> LineView:
        return LineView(
            name=self.catalog_label,
            href=self.catalog_href,
            image_url=self.image_url,
            metas=metas(
                meta(self.offer_label, META_OFFER),
                meta(self.price_label),
                meta(None if self.catalog_href else UNAVAILABLE_LABEL),
            ),
            aside=self.quantity_label,
        )


@dataclass(frozen=True, slots=True)
class PortalOrderDate:
    label: str
    value: datetime


@dataclass(frozen=True, slots=True)
class PortalOrderDetailContext:
    order: Order
    content_lines: tuple[PortalOrderContentLine, ...]
    contents_label: str
    dates: tuple[PortalOrderDate, ...]
    title: str
    customer_status_label: str
    status_icon: str
    cancel_url: str
    repeat_order_url: str

    def as_dict(self) -> dict[str, object]:
        return {
            "order": self.order,
            "content_lines": self.content_lines,
            "contents_label": self.contents_label,
            "dates": self.dates,
            "title": self.title,
            "customer_status_label": self.customer_status_label,
            "status_icon": self.status_icon,
            "cancel_url": self.cancel_url,
            "repeat_order_url": self.repeat_order_url,
        }


def build_portal_order_detail_context(
    *,
    order: Order,
    language_code: str,
) -> PortalOrderDetailContext:
    order_lines = tuple(
        order.lines
        .select_related(
            "product",
            "product__profile",
            "commercial_offer",
        )
        .order_by("id")
    )

    available_catalog_product_ids = {
        catalog_product.product.id
        for catalog_product in (
            list_business_catalog_products()
        )
    }

    content_lines = tuple(
        _build_content_line(
            line,
            language_code=language_code,
            currency=order.currency,
            available_catalog_product_ids=(
                available_catalog_product_ids
            ),
        )
        for line in order_lines
    )

    return PortalOrderDetailContext(
        order=order,
        content_lines=content_lines,
        contents_label=contents_summary(
            product_count=len(content_lines),
            total_quantity=sum(
                line.quantity
                for line in content_lines
            ),
        ),
        dates=_order_dates(
            order
        ),
        title=_(
            "Order #%(order_id)s"
        )
        % {
            "order_id": order.pk,
        },
        customer_status_label=(
            business_order_status_label(
                order.status
            )
        ),
        status_icon=order_status_icon(
            order.status
        ),
        cancel_url=reverse(
            "business_portal:orders"
        ),
        repeat_order_url=reverse(
            "business_portal:repeat_order",
            kwargs={
                "order_id": order.pk,
            },
        ),
    )


def _order_dates(
    order: Order,
) -> tuple[PortalOrderDate, ...]:
    """The steps the order has passed, in order; Created only before it
    was placed."""

    steps = (
        (_("Placed"), order.placed_at),
        (_("Prepared"), order.packed_at),
        (_("Delivered"), order.delivered_at),
        (_("Cancelled"), order.cancelled_at),
    )

    dates = tuple(
        PortalOrderDate(
            label=label,
            value=value,
        )
        for label, value in steps
        if value is not None
    )

    if order.placed_at is None:
        dates = (
            PortalOrderDate(
                label=_("Created"),
                value=order.created_at,
            ),
        ) + dates

    return dates


def _build_content_line(
    line: OrderLine,
    *,
    language_code: str,
    currency: str,
    available_catalog_product_ids: set[int],
) -> PortalOrderContentLine:
    presentation = business_order_line_presentation(
        line,
        language_code=language_code,
        currency=currency,
    )

    return PortalOrderContentLine(
        product=line.product,
        quantity=line.quantity_in_units,
        quantity_label=quantity_label(
            line.quantity_in_units
        ),
        unit=line.get_unit_display(),
        catalog_label=presentation.catalog_label,
        offer_label=presentation.offer_label,
        price_label=presentation.price_label,
        catalog_href=_catalog_product_href(
            product_id=line.product_id,
            available_catalog_product_ids=(
                available_catalog_product_ids
            ),
        ),
        image_url=product_image_url(
            line.product,
        ),
    )


def _catalog_product_href(
    *,
    product_id: int,
    available_catalog_product_ids: set[int],
) -> str | None:
    if product_id not in available_catalog_product_ids:
        return None

    return reverse(
        "business_portal:catalog_product",
        kwargs={
            "product_id": product_id,
        },
    )
