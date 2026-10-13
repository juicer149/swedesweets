from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

from accounts.roles import RoleSpec
from common.catalog.contracts import CatalogProduct
from common.detail_cards import (
    DetailAction,
    build_secondary_get_action,
)
from common.page_tabs import PageTab, TabAction
from inventory.expiry import ExpiryInfo, ExpiryState, build_expiry_info
from inventory.models import InventoryBatch
from ops_portal.inventory.access import can_create_batch
from ops_portal.products.access import (
    can_edit_product,
)
from ops_portal.products.catalog_preview import (
    CatalogPagePreview,
    build_catalog_page_previews,
)
from ops_portal.products.presentation import (
    ProductTagPresentation,
    product_attribute_tags,
    product_status_icon,
)
from ops_portal.products.pricing_forms import (
    variant_amounts,
)
from pricing.models import CommercialPrice
from products.images import product_display_url, product_image_url
from products.models import (
    Product,
    ProductProfile,
    ProductVariant,
)

PRODUCT_DETAIL_TABS = (
    # The product and what is sold (its variants and their prices), how
    # the shop shows it, then what is on the shelf (each variant's stock
    # and batches).
    PageTab(
        key="product",
        label="Product",
        icon="lollipop",
        template="ops_portal/products/includes/detail_tab_product.html",
    ),
    PageTab(
        key="catalog",
        label="Catalog",
        icon="image",
        template="ops_portal/products/includes/detail_tab_catalog.html",
    ),
    PageTab(
        key="inventory",
        label="Inventory",
        icon="inventory",
        template="ops_portal/products/includes/detail_tab_inventory.html",
    ),
)


@dataclass(frozen=True, slots=True)
class ProductProfileSummary:
    category: str
    category_label: str
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
            image_url="",
        )


@dataclass(frozen=True, slots=True)
class ChannelPrice:
    """A channel's price as the product page shows it: "55.00 € · 549.00
    kr", or "—"."""

    label: str
    amounts: str


@dataclass(frozen=True, slots=True)
class ChannelOffer:
    """A sales channel on a variant's card: its chip (on or off) and,
    when the variant is sold in it, its price beside the chip."""

    label: str
    sold: bool
    # "55.00 € · 549.00 kr"; empty when not sold in it.
    amounts: str


@dataclass(frozen=True, slots=True)
class BatchLink:
    """A batch on the shelf, in its variant's card on the Inventory tab:
    to its page, coloured by its best-before (inventory/expiry.py)."""

    batch_id: str
    best_before: date
    quantity_label: str
    href: str
    expiry: ExpiryInfo

    @property
    def expired(self) -> bool:
        """Past its best-before and still on the shelf (not closed)."""

        return self.expiry.state == ExpiryState.EXPIRED

    @property
    def tone(self) -> str:
        """Expired (red); critical or soon, within EXPIRY_SOON_DAYS
        (orange); else safe."""

        if self.expired:
            return "expired"

        if self.expiry.state in (ExpiryState.CRITICAL, ExpiryState.SOON):
            return "soon"

        return "safe"


@dataclass(frozen=True, slots=True)
class VariantCard:
    """A variant on the product page, as its card on the edit page: label,
    weight, sales channels, its prices (its stock is on the Inventory
    tab: VariantStock)."""

    label: str
    weight_label: str
    retail: bool
    business: bool
    paused: bool
    # Its prices in the channels it is sold in.
    prices: tuple[ChannelPrice, ...]
    # Its channels, Business over Retail, each with its price when sold.
    channels: tuple[ChannelOffer, ...]
    # Stock or orders: its weight can no longer change.
    weight_fixed: bool


@dataclass(frozen=True, slots=True)
class VariantStock:
    """A variant on the product page's Inventory tab: how many are in
    stock, and its batches on the shelf, the soonest best-before first."""

    label: str
    weight_label: str
    paused: bool
    stock_label: str
    in_stock: bool
    batches: tuple[BatchLink, ...]

    @property
    def has_expired_batch(self) -> bool:
        return any(batch.expired for batch in self.batches)


CHANNELS = (
    (CommercialPrice.Channel.RETAIL, "retail", "Retail"),
    (CommercialPrice.Channel.BUSINESS, "business", "Business"),
)

CURRENCY_SIGNS = (
    ("eur", "€"),
    ("sek", "kr"),
)


def _channel_price(
    amounts: dict[str, Decimal | None],
    *,
    key: str,
    label: str,
) -> ChannelPrice:
    parts = [
        f"{amounts[f'{key}_{currency}']:.2f} {sign}"
        for currency, sign in CURRENCY_SIGNS
        if amounts.get(f"{key}_{currency}") is not None
    ]

    return ChannelPrice(label=label, amounts=" · ".join(parts) or "—")


@dataclass(frozen=True, slots=True)
class ProductDetailContext:
    product: Product
    profile: ProductProfileSummary
    attribute_tags: tuple[
        ProductTagPresentation,
        ...,
    ]
    variant_cards: tuple[VariantCard, ...]
    variant_stocks: tuple[VariantStock, ...]
    catalog_previews: tuple[CatalogPagePreview, ...]
    in_shop: bool
    # The Catalog tab's label: "In shop", or what keeps it out.
    shop_label: str
    status_key: str
    status_label: str
    status_icon: str
    edit_action: DetailAction | None
    add_batch_href: str | None
    page_tabs: tuple[PageTab, ...]
    back_url: str
    title: str
    description: str
    cancel_url: str

    @property
    def tab_actions(self) -> tuple[TabAction, ...]:
        """At the section nav's right, the open tab's: Edit (the product's
        form on Product, the catalog's on Catalog), Add batch on
        Inventory."""

        actions = []

        if self.edit_action is not None:
            actions += [
                TabAction(tab="product", href=f"{self.edit_action.href}#product"),
                TabAction(tab="catalog", href=self.edit_catalog_href),
            ]

        if self.add_batch_href:
            actions.append(
                TabAction(
                    tab="inventory",
                    href=self.add_batch_href,
                    label="Add batch",
                    icon="plus",
                )
            )

        return tuple(actions)

    @property
    def edit_catalog_href(self) -> str:
        return reverse(
            "ops_products:edit_catalog",
            kwargs={"product_pk": self.product.pk},
        )

    def as_dict(
        self,
    ) -> dict[str, object]:
        return {
            "product": self.product,
            "profile": self.profile,
            "attribute_tags": (
                self.attribute_tags
            ),
            "variant_cards": self.variant_cards,
            "variant_stocks": self.variant_stocks,
            "catalog_previews": self.catalog_previews,
            "in_shop": self.in_shop,
            "shop_label": self.shop_label,
            "edit_catalog_href": self.edit_catalog_href,
            "status_key": self.status_key,
            "status_label": self.status_label,
            "status_icon": self.status_icon,
            # Its picture beside the name (status_heading.html).
            "heading_image_url": product_image_url(self.product) or "",
            "edit_action": self.edit_action,
            "add_batch_href": self.add_batch_href,
            "page_tabs": self.page_tabs,
            "tab_actions": self.tab_actions,
            "tabs_label": "Product sections",
            "back_url": self.back_url,
            "back_label": "Back to products",
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
    prices_by_channel: dict[str, dict[int, CommercialPrice]],
    role_spec: RoleSpec,
    cancel_url: str,
    stock_by_variant: dict[int, int] | None = None,
    batches_by_variant: dict[int, list[InventoryBatch]] | None = None,
    shop_product: CatalogProduct | None = None,
    today: date | None = None,
) -> ProductDetailContext:
    variants = list(product.variants.all())
    stock_by_variant = stock_by_variant or {}
    total_stock = sum(stock_by_variant.get(variant.pk, 0) for variant in variants)

    return ProductDetailContext(
        product=product,
        profile=(
            ProductProfileSummary
            .from_product(
                product
            )
        ),
        attribute_tags=(
            product_attribute_tags(
                product
            )
        ),
        variant_cards=build_variant_cards(
            variants=variants,
            prices_by_channel=prices_by_channel,
        ),
        variant_stocks=build_variant_stocks(
            product=product,
            variants=variants,
            stock_by_variant=stock_by_variant,
            batches_by_variant=batches_by_variant or {},
            today=today or timezone.localdate(),
        ),
        catalog_previews=build_catalog_page_previews(
            product=product,
            shop_product=shop_product,
        ),
        in_shop=shop_product is not None,
        shop_label=_shop_label(
            product=product,
            variants=variants,
            prices_by_channel=prices_by_channel,
            total_stock=total_stock,
            in_shop=shop_product is not None,
        ),
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
        add_batch_href=(
            f"{reverse('ops_inventory:create')}?product={product.pk}"
            if can_create_batch(role_spec=role_spec)
            else None
        ),
        page_tabs=PRODUCT_DETAIL_TABS,
        back_url=cancel_url,
        title=product.display_name,
        description="",
        cancel_url=cancel_url,
    )


def _shop_label(
    *,
    product: Product,
    variants: list[ProductVariant],
    prices_by_channel: dict[str, dict[int, CommercialPrice]],
    total_stock: int,
    in_shop: bool,
) -> str:
    """"In shop", or "Not in shop" and what keeps it out: inactive, no
    retail price in EUR, no stock (the shop's rules,
    retail.catalog_selectors)."""

    if in_shop:
        return "In shop"

    retail_offers = prices_by_channel.get(CommercialPrice.Channel.RETAIL, {})
    has_retail_price = any(
        variant.active
        and _enabled(retail_offers, variant)
        and variant_amounts(
            prices_by_channel=prices_by_channel,
            variant_id=variant.pk,
        )["retail_eur"]
        is not None
        for variant in variants
    )
    gaps = [
        reason
        for reason, missing in (
            ("inactive", not product.active),
            ("no retail price", not has_retail_price),
            ("no stock", total_stock <= 0),
        )
        if missing
    ]

    return " · ".join(["Not in shop", *gaps])


# A product with one variant (no label): what its card is called.
ONLY_VARIANT_NAME = "One variant"


def build_variant_cards(
    *,
    variants: list[ProductVariant],
    prices_by_channel: dict[str, dict[int, CommercialPrice]],
) -> tuple[VariantCard, ...]:
    """The product's variants in order, as on the edit page, each with its
    prices in the channels it is sold in."""

    cards = []

    for variant in variants:
        amounts = variant_amounts(
            prices_by_channel=prices_by_channel,
            variant_id=variant.pk,
        )
        sold = {
            key: variant.active
            and _enabled(prices_by_channel.get(channel, {}), variant)
            for channel, key, _label in CHANNELS
        }
        cards.append(
            VariantCard(
                label=variant.label or ONLY_VARIANT_NAME,
                weight_label=f"{variant.weight_per_unit} g",
                retail=sold["retail"],
                business=sold["business"],
                # Paused: switched off (both channels off on the edit page).
                paused=not variant.active,
                prices=tuple(
                    _channel_price(amounts, key=key, label=label)
                    for _channel, key, label in CHANNELS
                    if sold[key]
                ),
                channels=tuple(
                    ChannelOffer(
                        label=label,
                        sold=sold[key],
                        amounts=(
                            _channel_price(amounts, key=key, label=label).amounts
                            if sold[key]
                            else ""
                        ),
                    )
                    for _channel, key, label in reversed(CHANNELS)
                ),
                weight_fixed=(
                    variant.batches.exists()
                    or variant.order_lines.exists()
                ),
            )
        )

    return tuple(cards)


def build_variant_stocks(
    *,
    product: Product,
    variants: list[ProductVariant],
    stock_by_variant: dict[int, int],
    batches_by_variant: dict[int, list[InventoryBatch]],
    today: date,
) -> tuple[VariantStock, ...]:
    """The product's variants in order, each with its stock and its
    batches on the shelf (a batch past its best-before: expired)."""

    stocks = []

    for variant in variants:
        stock = stock_by_variant.get(variant.pk, 0)

        stocks.append(
            VariantStock(
                label=variant.label or ONLY_VARIANT_NAME,
                weight_label=f"{variant.weight_per_unit} g",
                paused=not variant.active,
                stock_label=product.stock_quantity_label(stock),
                in_stock=stock > 0,
                batches=tuple(
                    BatchLink(
                        batch_id=batch.batch_id,
                        best_before=batch.best_before,
                        quantity_label=product.stock_quantity_label(
                            batch.quantity
                        ),
                        href=reverse(
                            "ops_inventory:detail",
                            kwargs={"batch_pk": batch.pk},
                        ),
                        expiry=build_expiry_info(
                            best_before=batch.best_before,
                            today=today,
                        ),
                    )
                    for batch in batches_by_variant.get(variant.pk, [])
                ),
            )
        )

    return tuple(stocks)


def _enabled(
    offers: dict[int, CommercialPrice],
    variant: ProductVariant,
) -> bool:
    offer = offers.get(variant.pk)

    return offer is not None and offer.enabled


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


def _profile_original_image_url(
    profile: ProductProfile,
) -> str:
    """The large picture behind "Open image" (the display size)."""

    return product_display_url(profile) or ""


def _product_status_label(
    product: Product,
) -> str:
    return (
        "Active"
        if product.active
        else "Inactive"
    )
