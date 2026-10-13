from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

from accounts.roles import RoleSpec
from common.detail_cards import (
    DetailAction,
    build_secondary_get_action,
)
from common.page_tabs import PageTab, TabAction
from inventory.expiry import (
    ExpiryInfo,
    ExpiryState,
    build_expiry_info,
    is_orderable_best_before,
)
from inventory.models import InventoryBatch
from ops_portal.inventory.access import can_create_batch
from ops_portal.products.access import (
    can_edit_product,
)
from ops_portal.products.presentation import (
    ProductTagPresentation,
    product_attribute_tags,
    product_status_icon,
)
from ops_portal.products.pricing_forms import (
    variant_amounts,
)
from ops_portal.products.shop_text import LanguageText, build_language_texts
from pricing.models import CommercialPrice
from products.images import product_image_url
from products.models import (
    Product,
    ProductVariant,
)

PRODUCT_DETAIL_TABS = (
    # The product and what is sold (its variants and their prices), its
    # shop text, then what is on the shelf (each variant's batches).
    PageTab(
        key="product",
        label="Product",
        icon="lollipop",
        template="ops_portal/products/includes/detail_tab_product.html",
    ),
    PageTab(
        key="text",
        label="Shop text",
        icon="image",
        template="ops_portal/products/includes/detail_tab_text.html",
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

    @classmethod
    def from_product(
        cls,
        product: Product,
    ) -> ProductProfileSummary:
        profile = getattr(product, "profile", None)

        if profile is None or not profile.category:
            return cls(category="", category_label="")

        return cls(
            category=profile.category,
            category_label=profile.get_category_display(),
        )


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
    # In stock (on the shelf), and how many of them orders hold.
    quantity: int
    reserved: int
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
    weight, its sales channels with their prices (the Product tab); its
    batches on the shelf (the Inventory tab)."""

    label: str
    weight_label: str
    paused: bool
    # Its channels, Business over Retail, each with its price when sold.
    channels: tuple[ChannelOffer, ...]
    # Stock or orders: its weight can no longer change.
    weight_fixed: bool
    # On the shelf, the soonest best-before first.
    batches: tuple[BatchLink, ...]

    @property
    def is_sold(self) -> bool:
        return any(channel.sold for channel in self.channels)


CHANNELS = (
    (CommercialPrice.Channel.RETAIL, "retail", "Retail"),
    (CommercialPrice.Channel.BUSINESS, "business", "Business"),
)

CURRENCY_SIGNS = (
    ("eur", "€"),
    ("sek", "kr"),
)


def _channel_amounts(
    amounts: dict[str, Decimal | None],
    *,
    key: str,
) -> str:
    """A channel's price as the product page shows it: "55.00 € · 549.00
    kr", or "—"."""

    parts = [
        f"{amounts[f'{key}_{currency}']:.2f} {sign}"
        for currency, sign in CURRENCY_SIGNS
        if amounts.get(f"{key}_{currency}") is not None
    ]

    return " · ".join(parts) or "—"


@dataclass(frozen=True, slots=True)
class ProductDetailContext:
    product: Product
    profile: ProductProfileSummary
    attribute_tags: tuple[
        ProductTagPresentation,
        ...,
    ]
    variant_cards: tuple[VariantCard, ...]
    language_texts: tuple[LanguageText, ...]
    # For sale (active, a variant in a sales channel) with nothing to sell
    # (no stock, or only batches past their best-before).
    out_of_stock: bool
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
    def inventory_notes(self) -> tuple[str, ...]:
        """What the Inventory tab warns about, first: for sale with nothing
        to sell, and batches past their best-before still on the shelf."""

        notes = []

        if self.out_of_stock:
            notes.append(
                "Out of stock: it is for sale, but there is nothing to sell."
            )

        expired = sum(
            batch.expired
            for card in self.variant_cards
            for batch in card.batches
        )

        if expired:
            notes.append(
                "1 batch past best-before (in red): sell it off or close it."
                if expired == 1
                else f"{expired} batches past best-before (in red): sell "
                "them off or close them."
            )

        return tuple(notes)

    @property
    def tab_actions(self) -> tuple[TabAction, ...]:
        """At the page's foot, the open tab's: Edit (the product's form on
        Product, the shop text's on Shop text), Add batch on Inventory."""

        actions = []

        if self.edit_action is not None:
            actions += [
                TabAction(tab="product", href=f"{self.edit_action.href}#product"),
                TabAction(tab="text", href=self.edit_catalog_href),
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
            "language_texts": self.language_texts,
            "inventory_notes": self.inventory_notes,
            "status_key": self.status_key,
            "status_label": self.status_label,
            "status_icon": self.status_icon,
            # Its picture on its card (product_view_card.html).
            "heading_image_url": product_image_url(self.product) or "",
            # Who may edit: the Shop text tab's "Add … text".
            "edit_action": self.edit_action,
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
    batches_by_variant: dict[int, list[InventoryBatch]] | None = None,
    reserved_by_batch: dict[int, int] | None = None,
    today: date | None = None,
) -> ProductDetailContext:
    variants = list(product.variants.all())
    batches_by_variant = batches_by_variant or {}
    today = today or timezone.localdate()
    variant_cards = build_variant_cards(
        variants=variants,
        prices_by_channel=prices_by_channel,
        batches_by_variant=batches_by_variant,
        reserved_by_batch=reserved_by_batch or {},
        today=today,
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
        variant_cards=variant_cards,
        language_texts=build_language_texts(product),
        out_of_stock=_out_of_stock(
            product=product,
            variants=variants,
            variant_cards=variant_cards,
            batches_by_variant=batches_by_variant,
            today=today,
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


def _out_of_stock(
    *,
    product: Product,
    variants: list[ProductVariant],
    variant_cards: tuple[VariantCard, ...],
    batches_by_variant: dict[int, list[InventoryBatch]],
    today: date,
) -> bool:
    """For sale (active, a variant in a sales channel) with nothing to
    sell: no stock, or only batches past their best-before (the shop's
    rule, inventory/expiry.py)."""

    for_sale = product.active and any(card.is_sold for card in variant_cards)
    sellable_stock = sum(
        batch.quantity
        for variant in variants
        for batch in batches_by_variant.get(variant.pk, [])
        if is_orderable_best_before(best_before=batch.best_before, today=today)
    )

    return for_sale and sellable_stock <= 0


# A product with one variant (no label): what its card is called.
ONLY_VARIANT_NAME = "One variant"


def build_variant_cards(
    *,
    variants: list[ProductVariant],
    prices_by_channel: dict[str, dict[int, CommercialPrice]],
    batches_by_variant: dict[int, list[InventoryBatch]] | None = None,
    reserved_by_batch: dict[int, int] | None = None,
    today: date | None = None,
) -> tuple[VariantCard, ...]:
    """The product's variants in order, as on the edit page, each with its
    prices in the channels it is sold in and its batches on the shelf
    (`batches_by_variant`; how many of each orders hold:
    `reserved_by_batch`)."""

    batches_by_variant = batches_by_variant or {}
    reserved_by_batch = reserved_by_batch or {}
    today = today or timezone.localdate()
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
                # Paused: switched off (both channels off on the edit page).
                paused=not variant.active,
                channels=tuple(
                    ChannelOffer(
                        label=label,
                        sold=sold[key],
                        amounts=(
                            _channel_amounts(amounts, key=key)
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
                batches=tuple(
                    BatchLink(
                        batch_id=batch.batch_id,
                        best_before=batch.best_before,
                        quantity=batch.quantity,
                        reserved=reserved_by_batch.get(batch.pk, 0),
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


def _product_status_label(
    product: Product,
) -> str:
    return (
        "Active"
        if product.active
        else "Inactive"
    )
