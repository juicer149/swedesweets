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

Product image storage is intentionally handled separately by
products.image_services.
"""

from __future__ import annotations

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
