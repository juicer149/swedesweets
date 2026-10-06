from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from django.urls import reverse

from accounts.roles import RoleSpec
from common.detail_cards import (
    DetailAction,
    build_secondary_get_action,
)
from inventory.models import InventoryBatch
from ops_portal.products.access import (
    can_edit_product,
)
from ops_portal.products.presentation import (
    ProductTagPresentation,
    product_attribute_tags,
    product_status_icon,
)
from orders.product_demand import (
    ProductDeliveredDemandSummary,
)
from pricing.models import CommercialPrice
from products.models import (
    Product,
    ProductProfile,
)
from reservations.availability import AvailableStockRow


@dataclass(frozen=True, slots=True)
class ProductStockSummary:
    product: Product
    batch_count: int
    physical_quantity: int
    reserved_quantity: int
    available_quantity: int

    @property
    def physical_quantity_label(
        self,
    ) -> str:
        return (
            self.product
            .stock_quantity_label(
                self.physical_quantity
            )
        )

    @property
    def reserved_quantity_label(
        self,
    ) -> str:
        return (
            self.product
            .stock_quantity_label(
                self.reserved_quantity
            )
        )

    @property
    def available_quantity_label(
        self,
    ) -> str:
        return (
            self.product
            .stock_quantity_label(
                self.available_quantity
            )
        )

    @property
    def available_summary_label(self) -> str:
        """For the heading: "12 boxes available"."""

        return f"{self.available_quantity_label} available"

    @classmethod
    def empty(
        cls,
        *,
        product: Product,
    ) -> ProductStockSummary:
        return cls(
            product=product,
            batch_count=0,
            physical_quantity=0,
            reserved_quantity=0,
            available_quantity=0,
        )

    @classmethod
    def from_available_stock_row(
        cls,
        *,
        product: Product,
        row: AvailableStockRow | None,
    ) -> ProductStockSummary:
        if row is None:
            return cls.empty(
                product=product,
            )

        return cls(
            product=product,
            batch_count=row.batch_count,
            physical_quantity=(
                row.physical_quantity
            ),
            reserved_quantity=(
                row.reserved_quantity
            ),
            available_quantity=(
                row.available_quantity
            ),
        )


@dataclass(frozen=True, slots=True)
class ProductProfileSummary:
    category: str
    category_label: str
    description: str
    ingredients: str
    image_url: str

    @classmethod
    def from_product(
        cls,
        product: Product,
    ) -> ProductProfileSummary:
        try:
            profile = product.profile
        except (
            Product.profile
            .RelatedObjectDoesNotExist
        ):
            return cls.empty()

        return cls(
            category=profile.category,
            category_label=(
                profile.get_category_display()
                if profile.category
                else ""
            ),
            description=(
                profile.description
            ),
            ingredients=(
                profile.ingredients
            ),
            image_url=(
                _profile_original_image_url(
                    profile
                )
            ),
        )

    @classmethod
    def empty(
        cls,
    ) -> ProductProfileSummary:
        return cls(
            category="",
            category_label="",
            description="",
            ingredients="",
            image_url="",
        )


@dataclass(frozen=True, slots=True)
class ProductPriceAmountSummary:
    currency: str
    label: str


@dataclass(frozen=True, slots=True)
class ProductChannelPricingSummary:
    label: str
    configured: bool
    enabled: bool
    amounts: tuple[
        ProductPriceAmountSummary,
        ...,
    ]

    @property
    def status_label(
        self,
    ) -> str:
        if not self.configured:
            return "Not configured"

        return (
            "Active"
            if self.enabled
            else "Inactive"
        )

    @classmethod
    def from_commercial_price(
        cls,
        *,
        label: str,
        commercial_price: (
            CommercialPrice | None
        ),
    ) -> (
        ProductChannelPricingSummary
    ):
        if commercial_price is None:
            return cls(
                label=label,
                configured=False,
                enabled=False,
                amounts=(),
            )

        amounts = tuple(
            ProductPriceAmountSummary(
                currency=(
                    amount.currency
                ),
                label=(
                    f"{amount.price:.2f} "
                    f"{amount.currency}"
                ),
            )
            for amount
            in commercial_price.amounts.all()
        )

        return cls(
            label=label,
            configured=True,
            enabled=(
                commercial_price.enabled
            ),
            amounts=amounts,
        )


@dataclass(frozen=True, slots=True)
class ProductPricingSummary:
    business: (
        ProductChannelPricingSummary
    )
    retail: (
        ProductChannelPricingSummary
    )

    @property
    def channels(self) -> tuple[ProductChannelPricingSummary, ...]:
        """Business, then retail: one row each on the product page."""

        return (self.business, self.retail)

    @property
    def configured_count(
        self,
    ) -> int:
        return sum(
            (
                self.business.configured,
                self.retail.configured,
            )
        )

    @property
    def summary_label(
        self,
    ) -> str:
        if self.configured_count == 0:
            return "Not configured"

        if self.configured_count == 1:
            return "1 channel configured"

        return "2 channels configured"

    @classmethod
    def from_commercial_prices(
        cls,
        *,
        business_price: (
            CommercialPrice | None
        ),
        retail_price: (
            CommercialPrice | None
        ),
    ) -> ProductPricingSummary:
        return cls(
            business=(
                ProductChannelPricingSummary
                .from_commercial_price(
                    label="Business",
                    commercial_price=(
                        business_price
                    ),
                )
            ),
            retail=(
                ProductChannelPricingSummary
                .from_commercial_price(
                    label="Retail",
                    commercial_price=(
                        retail_price
                    ),
                )
            ),
        )


@dataclass(frozen=True, slots=True)
class ProductBatchRow:
    batch_id: str
    batch_href: str
    quantity: int
    quantity_label: str
    best_before: object
    location: str
    status: str

    @property
    def meta(self) -> str:
        """The grey line under the batch id: best before · location."""

        parts = [
            f"Best before {self.best_before:%Y-%m-%d}"
            if self.best_before
            else "",
            self.location,
        ]
        return " · ".join(part for part in parts if part)


@dataclass(frozen=True, slots=True)
class ProductDemandSummary:
    product: Product
    delivered_order_count: int
    delivered_quantity: int
    average_quantity_per_delivered_order: (
        Decimal
    )
    last_delivered_at: (
        datetime | None
    )

    @property
    def delivered_quantity_label(
        self,
    ) -> str:
        return (
            self.product
            .stock_quantity_label(
                self.delivered_quantity
            )
        )

    @property
    def average_quantity_per_delivered_order_label(
        self,
    ) -> str:
        value = (
            self.average_quantity_per_delivered_order
            .normalize()
        )

        if (
            value
            == value.to_integral_value()
        ):
            display_value = str(
                int(value)
            )
        else:
            display_value = (
                format(
                    value,
                    "f",
                )
                .rstrip("0")
                .rstrip(".")
            )

        unit = (
            self.product.stock_unit_singular
            if (
                self.average_quantity_per_delivered_order
                == 1
            )
            else (
                self.product
                .stock_unit_plural
            )
        )

        return (
            f"{display_value} {unit}"
        )

    @classmethod
    def from_delivered_demand_summary(
        cls,
        *,
        product: Product,
        summary: (
            ProductDeliveredDemandSummary
        ),
    ) -> ProductDemandSummary:
        return cls(
            product=product,
            delivered_order_count=(
                summary.delivered_order_count
            ),
            delivered_quantity=(
                summary.delivered_quantity
            ),
            average_quantity_per_delivered_order=(
                summary
                .average_quantity_per_delivered_order
            ),
            last_delivered_at=(
                summary.last_delivered_at
            ),
        )


@dataclass(frozen=True, slots=True)
class ProductDetailContext:
    product: Product
    profile: ProductProfileSummary
    pricing: ProductPricingSummary
    attribute_tags: tuple[
        ProductTagPresentation,
        ...,
    ]
    stock: ProductStockSummary
    batch_rows: list[ProductBatchRow]
    demand: ProductDemandSummary
    status_key: str
    status_label: str
    status_icon: str
    edit_action: DetailAction | None
    title: str
    description: str
    cancel_url: str

    def as_dict(
        self,
    ) -> dict[str, object]:
        return {
            "product": self.product,
            "profile": self.profile,
            "pricing": self.pricing,
            "attribute_tags": (
                self.attribute_tags
            ),
            "stock": self.stock,
            "batch_rows": (
                self.batch_rows
            ),
            "demand": self.demand,
            "status_key": self.status_key,
            "status_label": self.status_label,
            "status_icon": self.status_icon,
            "edit_action": self.edit_action,
            "title": self.title,
            "description": (
                self.description
            ),
            "cancel_url": (
                self.cancel_url
            ),
        }


def build_product_detail_context(
    *,
    product: Product,
    stock_row: AvailableStockRow | None,
    active_batches: list[
        InventoryBatch
    ],
    demand_summary: (
        ProductDeliveredDemandSummary
    ),
    business_price: (
        CommercialPrice | None
    ),
    retail_price: (
        CommercialPrice | None
    ),
    role_spec: RoleSpec,
    cancel_url: str,
) -> ProductDetailContext:
    stock = (
        ProductStockSummary
        .from_available_stock_row(
            product=product,
            row=stock_row,
        )
    )

    demand = (
        ProductDemandSummary
        .from_delivered_demand_summary(
            product=product,
            summary=demand_summary,
        )
    )

    pricing = (
        ProductPricingSummary
        .from_commercial_prices(
            business_price=(
                business_price
            ),
            retail_price=(
                retail_price
            ),
        )
    )

    return ProductDetailContext(
        product=product,
        profile=(
            ProductProfileSummary
            .from_product(
                product
            )
        ),
        pricing=pricing,
        attribute_tags=(
            product_attribute_tags(
                product
            )
        ),
        stock=stock,
        batch_rows=(
            _build_batch_rows(
                active_batches
            )
        ),
        demand=demand,
        status_key=(
            "active" if product.active else "inactive"
        ),
        status_label=_product_status_label(product),
        status_icon=product_status_icon(product),
        edit_action=next(
            iter(
                build_product_secondary_actions(
                    product=product,
                    role_spec=role_spec,
                )
            ),
            None,
        ),
        title=product.display_name,
        description="",
        cancel_url=cancel_url,
    )


def build_product_secondary_actions(
    *,
    product: Product,
    role_spec: RoleSpec,
) -> tuple[DetailAction, ...]:
    if not can_edit_product(
        product=product,
        role_spec=role_spec,
    ):
        return ()

    return (
        build_secondary_get_action(
            label="Edit product",
            href=reverse(
                "ops_products:edit",
                kwargs={
                    "product_pk": (
                        product.pk
                    ),
                },
            ),
        ),
    )


def _build_batch_rows(
    batches: list[InventoryBatch],
) -> list[ProductBatchRow]:
    rows: list[
        ProductBatchRow
    ] = []

    for batch in batches:
        batch_href = reverse(
            "ops_inventory:detail",
            kwargs={
                "batch_pk": (
                    batch.pk
                ),
            },
        )

        rows.append(
            ProductBatchRow(
                batch_id=(
                    batch.batch_id
                ),
                batch_href=(
                    batch_href
                ),
                quantity=(
                    batch.quantity
                ),
                quantity_label=(
                    batch.product
                    .stock_quantity_label(
                        batch.quantity
                    )
                ),
                best_before=(
                    batch.best_before
                ),
                location=(
                    batch.location
                ),
                status=(
                    batch
                    .get_status_display()
                ),
            )
        )

    return rows


def _profile_original_image_url(
    profile: ProductProfile,
) -> str:
    if profile.image:
        return profile.image.url
    return ""


def _product_status_label(
    product: Product,
) -> str:
    return (
        "Active"
        if product.active
        else "Inactive"
    )
