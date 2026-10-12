"""
Product application services.

public API:
    create_product(...)
        -> Create product or return existing product with same SKU/internal
           number. A new product gets its only variant (Product.save).

    update_product(...)
        -> Update editable product catalog fields and profile data.

    update_product_active(...)
        -> Compatibility wrapper for status-only updates.

    add_variant(...)
        -> Add a variant (a size, a weight) to a product; the first one gets
           its label at the same time.

    rename_variant(...)
        -> Change a variant's label (its SKU stays).

    set_variant_weight(...), set_variant_active(...), delete_variant(...),
    reorder_variants(...)
        -> The rest of a variant's life, under rules 1 and 5-7
           (docs/product-variants.md).

    variant_has_history(variant) -> bool
        -> Whether a batch, a price or an order line ever used it.

    save_variants(product=..., changes=[VariantChange, ...])
        -> Apply a whole Variants tab at once: labels, weights, on sale or
           paused, new and deleted variants, and their order.

Product image storage is intentionally handled separately by
products.image_services.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.db import (
    IntegrityError,
    transaction,
)
from django.db.models import Max

from common.results import ServiceResult
from products.catalog import (
    make_sku,
    normalize_optional_text,
    normalize_required_text,
    normalize_variant_label,
    slugify_sku_part,
    validate_internal_number,
    validate_weight_per_unit,
)
from products.errors import (
    InvalidProductData,
)
from products.models import (
    Product,
    ProductProfile,
    ProductTranslation,
    ProductVariant,
)

CUSTOMER_FACING_LANGUAGE_CODE = "fr"


@transaction.atomic
def create_product(
    *,
    brand: str,
    name: str,
    weight_per_unit: int,
    stock_unit: str = Product.StockUnit.BOX,
    internal_number: int | None = None,
    manufacturer: str = "",
    vegan: bool = False,
    customer_facing_name_fr: str = "",
    category: str = "",
    description: str = "",
    ingredients: str = "",
    user=None,
) -> ServiceResult[Product]:
    """Create product or return existing product."""

    normalized_brand = (
        normalize_required_text(
            brand,
            field_name="brand",
        )
    )

    normalized_name = (
        normalize_required_text(
            name,
            field_name="name",
        )
    )

    normalized_manufacturer = (
        normalize_optional_text(
            manufacturer,
            field_name="manufacturer",
        )
    )

    validate_weight_per_unit(
        weight_per_unit
    )
    validate_internal_number(
        internal_number
    )
    _validate_stock_unit(
        stock_unit
    )
    _validate_profile_category(
        category
    )

    sku = make_sku(
        internal_number=internal_number,
        brand=normalized_brand,
        name=normalized_name,
        weight_per_unit=weight_per_unit,
    )

    existing = (
        Product.objects
        .filter(
            sku=sku
        )
        .first()
    )

    if existing is not None:
        return ServiceResult(
            item=existing,
            message=(
                "Product already exists in the catalog."
            ),
            created=False,
        )

    if internal_number is not None:
        existing = (
            Product.objects
            .filter(
                internal_number=(
                    internal_number
                )
            )
            .first()
        )

        if existing is not None:
            return ServiceResult(
                item=existing,
                message=(
                    "Product already exists in the catalog."
                ),
                created=False,
            )

    try:
        product = Product.objects.create(
            internal_number=internal_number,
            manufacturer=(
                normalized_manufacturer
            ),
            brand=normalized_brand,
            name=normalized_name,
            weight_per_unit=(
                weight_per_unit
            ),
            stock_unit=stock_unit,
            vegan=vegan,
        )

    except IntegrityError as exc:
        existing = (
            Product.objects
            .filter(
                sku=sku
            )
            .first()
        )

        if existing is not None:
            return ServiceResult(
                item=existing,
                message=(
                    "Product already exists in the catalog."
                ),
                created=False,
            )

        raise InvalidProductData(
            (
                "Could not create product "
                f"with SKU {sku}"
            )
        ) from exc

    product.mark_as_created(
        user=user
    )

    _set_product_profile(
        product=product,
        category=category,
        description=description,
        ingredients=ingredients,
    )

    set_product_translation(
        product=product,
        language_code=(
            CUSTOMER_FACING_LANGUAGE_CODE
        ),
        name=customer_facing_name_fr,
    )

    return ServiceResult(
        item=product,
        message=(
            "Product added to the catalog."
        ),
        created=True,
    )


@transaction.atomic
def update_product(
    *,
    product: Product,
    internal_number: int | None,
    manufacturer: str,
    brand: str,
    name: str,
    active: bool,
    vegan: bool,
    customer_facing_name_fr: str = "",
    category: str = "",
    description: str = "",
    ingredients: str = "",
    user=None,
) -> Product:
    """Update editable product catalog and profile data."""

    product = (
        Product.objects
        .select_for_update()
        .get(
            pk=product.pk
        )
    )

    old_active = product.active

    validate_internal_number(
        internal_number
    )
    _validate_profile_category(
        category
    )

    if internal_number is not None:
        number_is_taken = (
            Product.objects
            .filter(
                internal_number=(
                    internal_number
                )
            )
            .exclude(
                pk=product.pk
            )
            .exists()
        )

        if number_is_taken:
            raise InvalidProductData(
                (
                    f"Product number {internal_number} "
                    "already exists"
                )
            )

    product.internal_number = (
        internal_number
    )

    product.manufacturer = (
        normalize_optional_text(
            manufacturer,
            field_name="manufacturer",
        )
    )

    product.brand = (
        normalize_required_text(
            brand,
            field_name="brand",
        )
    )

    product.name = (
        normalize_required_text(
            name,
            field_name="name",
        )
    )

    product.active = active
    product.vegan = vegan

    try:
        product.save(
            update_fields=[
                "internal_number",
                "manufacturer",
                "brand",
                "name",
                "active",
                "vegan",
                "updated_at",
            ]
        )

    except IntegrityError as exc:
        raise InvalidProductData(
            "Could not update product"
        ) from exc

    product.mark_as_edited(
        user=user
    )

    product.mark_active_changed(
        old_active=old_active,
        user=user,
    )

    _set_product_profile(
        product=product,
        category=category,
        description=description,
        ingredients=ingredients,
    )

    set_product_translation(
        product=product,
        language_code=(
            CUSTOMER_FACING_LANGUAGE_CODE
        ),
        name=customer_facing_name_fr,
    )

    return product


@transaction.atomic
def update_product_active(
    *,
    product: Product,
    active: bool,
    user=None,
) -> Product:
    """Update mutable catalog status."""

    product = (
        Product.objects
        .select_for_update()
        .get(
            pk=product.pk
        )
    )

    old_active = product.active

    product.active = active

    product.save(
        update_fields=[
            "active",
            "updated_at",
        ]
    )

    product.mark_as_edited(
        user=user
    )

    product.mark_active_changed(
        old_active=old_active,
        user=user,
    )

    return product


@transaction.atomic
def add_variant(
    *,
    product: Product,
    label: str,
    first_label: str = "",
    weight_per_unit: int | None = None,
) -> ProductVariant:
    """Add a variant to a product, last in order.

    A product with only an unlabelled variant must name that one too
    (`first_label`, e.g. "M" when adding "L"): with more than one variant
    every one has a label (docs/product-variants.md, rule 2). Its SKU stays
    the product's; the new variant's is the product's SKU plus the label.
    The weight defaults to the product's.
    """

    product = Product.objects.select_for_update().get(pk=product.pk)
    variants = list(product.variants.order_by("position", "pk"))

    label = normalize_variant_label(label)

    if not label:
        raise InvalidProductData(
            "a new variant needs a label"
        )

    if len(variants) == 1 and not variants[0].label:
        rename_variant(
            variant=variants[0],
            label=first_label,
            required=True,
        )

    sku = f"{product.sku}-{slugify_sku_part(label)}"

    if ProductVariant.objects.filter(sku=sku).exists():
        raise InvalidProductData(
            f"a variant with SKU {sku} already exists"
        )

    next_position = (
        product.variants.aggregate(last=Max("position"))["last"] or 0
    ) + 1

    try:
        with transaction.atomic():
            return ProductVariant.objects.create(
                product=product,
                label=label,
                position=next_position,
                sku=sku,
                weight_per_unit=(
                    weight_per_unit
                    if weight_per_unit is not None
                    else product.weight_per_unit
                ),
            )
    except IntegrityError as exc:
        raise InvalidProductData(
            f"{product.display_name} already has a variant {label}"
        ) from exc


@transaction.atomic
def rename_variant(
    *,
    variant: ProductVariant,
    label: str,
    required: bool = False,
) -> ProductVariant:
    """Change a variant's label; its SKU stays. A product with several
    variants keeps a label on each (rule 2), so the label may be empty only
    for a product's only variant."""

    label = normalize_variant_label(label)

    if required and not label:
        raise InvalidProductData(
            "name the product's current variant too "
            "(first_label) before adding another"
        )

    variant.label = label

    try:
        with transaction.atomic():
            variant.save(update_fields=["label", "updated_at"])
    except IntegrityError as exc:
        raise InvalidProductData(
            f"{variant.product.display_name} already has a variant {label}"
        ) from exc

    return variant


def variant_has_history(
    variant: ProductVariant,
) -> bool:
    """A batch, a price (and so maybe a cart line) or an order line ever
    used this variant: its weight is fixed and it can only be paused, not
    deleted (rules 5 and 6)."""

    return (
        variant.batches.exists()
        or variant.commercial_prices.exists()
        or variant.order_lines.exists()
    )


def _variant_is_stocked_or_ordered(
    variant: ProductVariant,
) -> bool:
    return (
        variant.batches.exists()
        or variant.order_lines.exists()
    )


@transaction.atomic
def set_variant_weight(
    *,
    variant: ProductVariant,
    weight_per_unit: int,
) -> ProductVariant:
    """Change a variant's weight, only while no batch or order line uses
    it (rule 5): stock already counted and orders already placed are in
    the old weight."""

    if weight_per_unit == variant.weight_per_unit:
        return variant

    if _variant_is_stocked_or_ordered(variant):
        raise InvalidProductData(
            f"{variant.display_name} has stock or orders: its weight "
            "can no longer change"
        )

    variant.weight_per_unit = weight_per_unit
    variant.save(update_fields=["weight_per_unit", "updated_at"])

    return variant


@transaction.atomic
def set_variant_active(
    *,
    variant: ProductVariant,
    active: bool,
) -> ProductVariant:
    """Pause a variant (left out of catalogs, new batches and new orders)
    or bring it back. An active product keeps at least one active variant
    (rule 7): to stop selling it all, pause the product."""

    if variant.active == active:
        return variant

    product = Product.objects.select_for_update().get(pk=variant.product_id)

    if (
        not active
        and product.active
        and not product.variants.filter(active=True)
        .exclude(pk=variant.pk)
        .exists()
    ):
        raise InvalidProductData(
            f"{variant.display_name} is the last variant on sale: pause "
            "the product instead"
        )

    variant.active = active
    variant.save(update_fields=["active", "updated_at"])

    return variant


@transaction.atomic
def delete_variant(
    *,
    variant: ProductVariant,
) -> None:
    """Delete a variant nothing has used yet (rule 6; one with history can
    only be paused). A product keeps at least one variant (rule 1)."""

    product = Product.objects.select_for_update().get(pk=variant.product_id)

    if variant_has_history(variant):
        raise InvalidProductData(
            f"{variant.display_name} has been used: pause it instead"
        )

    if not product.variants.exclude(pk=variant.pk).exists():
        raise InvalidProductData(
            "a product keeps at least one variant"
        )

    if (
        product.active
        and variant.active
        and not product.variants.filter(active=True)
        .exclude(pk=variant.pk)
        .exists()
    ):
        raise InvalidProductData(
            f"{variant.display_name} is the last variant on sale: pause "
            "the product instead"
        )

    variant.delete()


@transaction.atomic
def reorder_variants(
    *,
    product: Product,
    variant_ids: list[int],
) -> None:
    """Put a product's variants in this order (positions 1, 2, 3 …). The
    list names each of its variants once."""

    current_ids = set(
        product.variants.values_list("pk", flat=True)
    )

    if len(variant_ids) != len(set(variant_ids)) or set(
        variant_ids
    ) != current_ids:
        raise InvalidProductData(
            "the new order must name each of the product's variants once"
        )

    variants = {
        variant.pk: variant
        for variant in product.variants.select_for_update()
    }

    for position, variant_id in enumerate(variant_ids, start=1):
        variant = variants[variant_id]

        if variant.position != position:
            variant.position = position
            variant.save(update_fields=["position", "updated_at"])


@dataclass(frozen=True, slots=True)
class VariantChange:
    """One row of the Variants tab, in the order wanted. variant_id None:
    a new variant."""

    variant_id: int | None
    label: str
    weight_per_unit: int
    active: bool = True
    delete: bool = False


@transaction.atomic
def save_variants(
    *,
    product: Product,
    changes: list[VariantChange],
) -> None:
    """Apply a product's Variants tab: every existing variant once, plus
    any new ones, in the order wanted.

    Labels are moved aside first (so two variants can swap names), new
    variants added, deleted ones removed, then the final labels, weights,
    pauses and order set, each through the rules above.
    """

    product = Product.objects.select_for_update().get(pk=product.pk)
    existing = {
        variant.pk: variant
        for variant in product.variants.select_for_update()
    }

    changes = [
        VariantChange(
            variant_id=change.variant_id,
            label=normalize_variant_label(change.label),
            weight_per_unit=change.weight_per_unit,
            active=change.active,
            delete=change.delete,
        )
        for change in changes
    ]

    named_ids = [
        change.variant_id
        for change in changes
        if change.variant_id is not None
    ]

    if sorted(named_ids) != sorted(existing):
        raise InvalidProductData(
            "the variants changed meanwhile: reload the page"
        )

    kept = [change for change in changes if not change.delete]

    if not kept:
        raise InvalidProductData(
            "a product keeps at least one variant"
        )

    if len(kept) > 1 and any(not change.label for change in kept):
        raise InvalidProductData(
            "with more than one variant, each needs a label"
        )

    labels = [change.label.casefold() for change in kept]

    if len(labels) != len(set(labels)):
        raise InvalidProductData(
            "two variants have the same label"
        )

    # Resume first, so a pause or a delete below never meets "the last
    # one on sale" while another is about to come back.
    for change in kept:
        variant = existing.get(change.variant_id)

        if variant is not None and change.active and not variant.active:
            set_variant_active(variant=variant, active=True)

    # Move changed and leaving labels aside: unique, never empty.
    for change in changes:
        variant = existing.get(change.variant_id)

        if variant is not None and (
            change.delete or variant.label != change.label
        ):
            variant.label = f"~{variant.pk}"
            variant.save(update_fields=["label", "updated_at"])

    order: list[int] = []

    for change in changes:
        if change.delete:
            continue

        if change.variant_id is None:
            variant = add_variant(
                product=product,
                label=change.label,
                weight_per_unit=change.weight_per_unit,
            )
            existing[variant.pk] = variant
            order.append(variant.pk)
        else:
            order.append(change.variant_id)

    for change in changes:
        if change.delete:
            delete_variant(variant=existing.pop(change.variant_id))

    for change, variant_id in zip(kept, order, strict=True):
        variant = existing[variant_id]

        if variant.label != change.label:
            variant.label = change.label
            variant.save(update_fields=["label", "updated_at"])

        set_variant_weight(
            variant=variant,
            weight_per_unit=change.weight_per_unit,
        )

    for change, variant_id in zip(kept, order, strict=True):
        if not change.active:
            set_variant_active(
                variant=existing[variant_id],
                active=False,
            )

    reorder_variants(product=product, variant_ids=order)


def set_product_translation(
    *,
    product: Product,
    language_code: str,
    name: str,
) -> ProductTranslation | None:
    normalized_name = (
        normalize_optional_text(
            name,
            field_name=(
                "customer-facing name"
            ),
        )
    )

    if not normalized_name:
        (
            ProductTranslation.objects
            .filter(
                product=product,
                language_code=(
                    language_code
                ),
            )
            .delete()
        )

        return None

    translation, _created = (
        ProductTranslation.objects
        .update_or_create(
            product=product,
            language_code=(
                language_code
            ),
            defaults={
                "name": normalized_name,
            },
        )
    )

    return translation


def _set_product_profile(
    *,
    product: Product,
    category: str,
    description: str,
    ingredients: str,
) -> ProductProfile:
    _validate_profile_category(
        category
    )

    profile, _created = (
        ProductProfile.objects
        .select_for_update()
        .get_or_create(
            product=product
        )
    )

    profile.category = category
    profile.description = (
        description.strip()
    )
    profile.ingredients = (
        ingredients.strip()
    )

    profile.save(
        update_fields=[
            "category",
            "description",
            "ingredients",
        ]
    )

    return profile


def _validate_profile_category(
    category: str,
) -> None:
    valid_categories = {
        choice.value
        for choice
        in ProductProfile.Category
    }

    if (
        category
        and category not in valid_categories
    ):
        raise InvalidProductData(
            (
                "Unsupported product category: "
                f"{category}"
            )
        )


def _validate_stock_unit(
    stock_unit: str,
) -> None:
    valid_units = {
        choice.value
        for choice
        in Product.StockUnit
    }

    if stock_unit not in valid_units:
        raise InvalidProductData(
            (
                "Unsupported stock unit: "
                f"{stock_unit}"
            )
        )
