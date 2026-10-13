from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.urls import reverse

from accounts.roles import RoleSpec
from common.catalog.contracts import CatalogProduct
from common.detail_cards import (
    DetailAction,
    build_secondary_get_action,
)
from common.page_tabs import PageTab
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
    product_amounts,
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
class VariantCard:
    """A variant on the product page, as its card on the edit page: label,
    weight, sales channels, its own prices (when it has some), stock."""

    label: str
    weight_label: str
    retail: bool
    business: bool
    paused: bool
    # Its prices in the channels it is sold in, when unlike the
    # product's; empty: it sells at the product's price.
    own_prices: tuple[ChannelPrice, ...]
    stock_label: str
    in_stock: bool
    # Stock or orders: its weight can no longer change.
    weight_fixed: bool


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
    product_price: tuple[ChannelPrice, ...]
    variant_cards: tuple[VariantCard, ...]
    catalog_previews: tuple[CatalogPagePreview, ...]
    in_shop: bool
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

    def as_dict(
        self,
    ) -> dict[str, object]:
        return {
            "product": self.product,
            "profile": self.profile,
            "attribute_tags": (
                self.attribute_tags
            ),
            "product_price": self.product_price,
            "variant_cards": self.variant_cards,
            "catalog_previews": self.catalog_previews,
            "in_shop": self.in_shop,
            "edit_catalog_href": reverse(
                "ops_products:edit_catalog",
                kwargs={"product_pk": self.product.pk},
            ),
            "status_key": self.status_key,
            "status_label": self.status_label,
            "status_icon": self.status_icon,
            # Its picture beside the name (status_heading.html).
            "heading_image_url": product_image_url(self.product) or "",
            "edit_action": self.edit_action,
            "add_batch_href": self.add_batch_href,
            "page_tabs": self.page_tabs,
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
    shop_product: CatalogProduct | None = None,
) -> ProductDetailContext:
    variants = list(product.variants.all())
    shared = product_amounts(
        prices_by_channel=prices_by_channel,
        variant_ids=[variant.pk for variant in variants],
    )

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
        product_price=tuple(
            _channel_price(shared, key=key, label=label)
            for _channel, key, label in CHANNELS
        ),
        variant_cards=build_variant_cards(
            product=product,
            variants=variants,
            prices_by_channel=prices_by_channel,
            shared=shared,
            stock_by_variant=stock_by_variant or {},
        ),
        catalog_previews=build_catalog_page_previews(
            product=product,
            shop_product=shop_product,
        ),
        in_shop=shop_product is not None,
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


# A product with one variant (no label): what its card is called.
ONLY_VARIANT_NAME = "One variant"


def build_variant_cards(
    *,
    product: Product,
    variants: list[ProductVariant],
    prices_by_channel: dict[str, dict[int, CommercialPrice]],
    shared: dict[str, Decimal | None],
    stock_by_variant: dict[int, int],
) -> tuple[VariantCard, ...]:
    """The product's variants in order, as on the edit page: a variant has
    its own prices when one of them is unlike the product's (the same rule
    as the edit form's price tag, variant_forms.build_variant_formset)."""

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
        own = any(
            value is not None and value != shared[field_name]
            for field_name, value in amounts.items()
        )
        stock = stock_by_variant.get(variant.pk, 0)

        cards.append(
            VariantCard(
                label=variant.label or ONLY_VARIANT_NAME,
                weight_label=f"{variant.weight_per_unit} g",
                retail=sold["retail"],
                business=sold["business"],
                # Paused: switched off (both channels off on the edit page).
                paused=not variant.active,
                own_prices=(
                    tuple(
                        _channel_price(amounts, key=key, label=label)
                        for _channel, key, label in CHANNELS
                        if sold[key]
                    )
                    if own
                    else ()
                ),
                stock_label=product.stock_quantity_label(stock),
                in_stock=stock > 0,
                weight_fixed=(
                    variant.batches.exists()
                    or variant.order_lines.exists()
                ),
            )
        )

    return tuple(cards)


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
