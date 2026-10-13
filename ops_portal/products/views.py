from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.urls import reverse

from accounts.password_again import PasswordAgainForm
from common.table_controls import (
    TableControls,
    TableControlsTemplate,
    TableFilter,
    TableSortField,
)
from inventory.selectors import (
    physical_quantity_by_variant,
    shelf_batches_by_variant,
)
from ops_portal.products.catalog_forms import (
    build_catalog_languages,
)
from ops_portal.products.detail_viewmodels import (
    build_product_detail_context,
)
from ops_portal.products.form_viewmodels import (
    build_catalog_form_context,
    build_create_product_form_context,
    build_edit_product_form_context,
)
from ops_portal.products.forms import (
    ProductEditForm,
    ProductForm,
    build_product_edit_initial_data,
)
from ops_portal.products.list_viewmodels import (
    build_product_page_rows,
    build_product_quick_jump_search,
    build_products_page_header,
)
from ops_portal.products.price_check import (
    PriceCheck,
    check_is_on,
    price_changes,
)
from ops_portal.products.pricing_forms import (
    ProductPricingForm,
)
from ops_portal.products.variant_forms import (
    build_variant_formset,
)
from pricing.errors import (
    InvalidCommercialPrice,
)
from pricing.models import CommercialPrice
from pricing.product_configuration import (
    VariantPricing,
    update_product_standard_pricing,
    update_variants_pricing,
)
from pricing.selectors import (
    standard_prices_by_variant_id,
)
from products.errors import (
    InvalidProductData,
)
from products.image_services import (
    ProductImageChange,
    change_product_image,
)
from products.models import Product
from products.selectors import (
    DEFAULT_PRODUCT_SORT,
    PRODUCT_FILTER_ACTIVE,
    PRODUCT_FILTER_ALL,
    PRODUCT_FILTER_INACTIVE,
    PRODUCT_SORTS,
    list_products,
)
from products.services import (
    create_product,
    save_variants,
    update_product,
    update_product_catalog,
)
from reservations.api import active_reserved_quantities_by_batch_pk
from retail.catalog_selectors import (
    get_retail_catalog_product,
)

PRODUCT_FILTERS = [
    TableFilter(
        PRODUCT_FILTER_ALL,
        "All",
    ),
    TableFilter(
        PRODUCT_FILTER_ACTIVE,
        "Active",
    ),
    TableFilter(
        PRODUCT_FILTER_INACTIVE,
        "Inactive",
    ),
]

PRODUCT_TABLE_SORTS = [
    TableSortField(
        "number",
        "#",
    ),
    TableSortField(
        "product",
        "Product",
    ),
    TableSortField(
        "brand",
        "Brand",
    ),
    TableSortField(
        "manufacturer",
        "Manufacturer",
    ),
    TableSortField(
        "weight",
        "Weight",
    ),
    TableSortField(
        "vegan",
        "Vegan",
    ),
    TableSortField(
        "status",
        "Status",
    ),
]

PRODUCTS_LIST_ANCHOR = (
    "products-list"
)
PRODUCT_FILTER_QUERY_KEY = (
    "status"
)

PRODUCT_TABLE_CONTROLS_TEMPLATE = (
    TableControlsTemplate(
        filters_title_id=(
            "products-filters-title"
        ),
        filters_aria_label=(
            "Product filters"
        ),
        sort_title_id=(
            "products-sort-title"
        ),
        sort_select_id=(
            "mobile-product-sort"
        ),
    )
)


@login_required
def index(request):
    controls = (
        TableControls
        .from_request_values(
            base_path=request.path,
            anchor=(
                PRODUCTS_LIST_ANCHOR
            ),
            requested_filter=(
                request.GET.get(
                    PRODUCT_FILTER_QUERY_KEY,
                    "",
                )
            ),
            requested_sort=(
                request.GET.get(
                    "sort",
                    "",
                )
            ),
            filters=PRODUCT_FILTERS,
            allowed_sorts=PRODUCT_SORTS,
            default_sort=(
                DEFAULT_PRODUCT_SORT
            ),
            filter_query_key=(
                PRODUCT_FILTER_QUERY_KEY
            ),
        )
    )

    products = list(
        list_products(
            status=(
                controls.active_filter
            ),
            sort=(
                controls.active_sort
            ),
        )
    )

    product_rows = (
        build_product_page_rows(
            products
        )
    )

    context = {
        "page_header": (
            build_products_page_header(
                role_spec=(
                    request.role_spec
                ),
            )
        ),
        "product_rows": (
            product_rows
        ),
        "quick_jump_search": (
            build_product_quick_jump_search(
                product_rows
            )
        ),
        "filters": (
            controls
            .build_filter_links(
                PRODUCT_FILTERS
            )
        ),
        "table_sorts": (
            controls
            .build_table_sort_links(
                PRODUCT_TABLE_SORTS
            )
        ),
        "mobile_sort_fields": (
            controls
            .build_mobile_sort_fields(
                PRODUCT_TABLE_SORTS
            )
        ),
        "mobile_sort_direction": (
            controls
            .build_mobile_sort_direction()
        ),
        "table_controls_template": (
            PRODUCT_TABLE_CONTROLS_TEMPLATE
        ),
        "numeric_table_fields": [
            "number",
            "weight",
        ],
    }

    return render(
        request,
        "ops_portal/products/index.html",
        context,
    )


@login_required
def detail(
    request,
    product_pk: int,
):
    product = _get_product_or_404(
        product_pk
    )
    batches_by_variant = shelf_batches_by_variant(product=product)

    context = (
        build_product_detail_context(
            product=product,
            prices_by_channel=_standard_prices_by_channel(product),
            role_spec=request.role_spec,
            cancel_url=reverse(
                "ops_products:index"
            ),
            stock_by_variant=physical_quantity_by_variant(
                product=product,
            ),
            batches_by_variant=batches_by_variant,
            # How many of each batch orders hold (the Inventory tab).
            reserved_by_batch=active_reserved_quantities_by_batch_pk(
                batch_pks=[
                    batch.pk
                    for batches in batches_by_variant.values()
                    for batch in batches
                ],
            ),
            shop_product=get_retail_catalog_product(
                product_id=product.pk,
            ),
        )
        .as_dict()
    )

    return render(
        request,
        (
            "ops_portal/products/"
            "detail.html"
        ),
        context,
    )


@login_required
def edit(
    request,
    product_pk: int,
):
    """The product's own data (with its category and picture) and its
    variants with their sales channels and prices, saved together; the page
    comes back after a save. Big price changes wait for the user's password
    (price_check.py)."""

    product = _get_product_or_404(
        product_pk
    )

    prices_by_channel = _standard_prices_by_channel(product)
    price_check = None

    if request.method == "POST":
        form = ProductEditForm(
            request.POST,
            request.FILES,
            product=product,
        )
        variant_formset = build_variant_formset(
            product=product,
            data=request.POST,
            prices_by_channel=prices_by_channel,
        )

        forms_are_valid = all(
            [
                form.is_valid(),
                variant_formset.is_valid(),
            ]
        ) and _prices_are_complete(variant_formset)

        if forms_are_valid and check_is_on():
            changes = price_changes(
                prices_by_channel=prices_by_channel,
                variant_formset=variant_formset,
            )
            check_form = PasswordAgainForm(request.POST, user=request.user)

            if changes and not check_form.is_confirmed():
                price_check = PriceCheck(changes=changes, form=check_form)

        if forms_are_valid and price_check is None:
            image_change = ProductImageChange.empty()

            try:
                with transaction.atomic():
                    updated_product = update_product(
                        product=product,
                        internal_number=form.cleaned_data["internal_number"],
                        manufacturer=form.cleaned_data["manufacturer"],
                        brand=form.cleaned_data["brand"],
                        name=form.cleaned_data["name"],
                        active=form.active_value,
                        vegan=form.cleaned_data["vegan"],
                        user=request.user,
                    )

                    save_variants(
                        product=updated_product,
                        changes=variant_formset.changes(),
                    )

                    update_variants_pricing(
                        product=updated_product,
                        pricing=_pricing_by_variant_id(
                            product=updated_product,
                            variant_formset=variant_formset,
                        ),
                    )

                    update_product_catalog(
                        product=updated_product,
                        category=form.cleaned_data["category"],
                        user=request.user,
                    )

                    # A new picture replaces the old one; the old files go
                    # once everything is saved (commit below).
                    image_change = change_product_image(
                        product=updated_product,
                        uploaded_image=form.cleaned_data["image"],
                        remove_image=False,
                    )

            except InvalidProductData as error:
                image_change.rollback()
                form.add_error(
                    None,
                    str(error),
                )

            except InvalidCommercialPrice as error:
                image_change.rollback()
                form.add_error(
                    None,
                    str(error),
                )

            except Exception:
                image_change.rollback()
                raise

            else:
                image_change.commit()

                messages.success(
                    request,
                    f"Product {updated_product.sku} updated.",
                )

                # Saved, and still here.
                return redirect(
                    "ops_products:edit",
                    product_pk=updated_product.pk,
                )

    else:
        form = ProductEditForm(
            initial=build_product_edit_initial_data(product),
            product=product,
        )
        variant_formset = build_variant_formset(
            product=product,
            prices_by_channel=prices_by_channel,
        )

    context = (
        build_edit_product_form_context(
            form=form,
            product=product,
            variant_formset=variant_formset,
            price_check=price_check,
        )
        .as_dict()
    )

    return render(
        request,
        "ops_portal/products/product_form.html",
        context,
    )


def _standard_prices_by_channel(
    product: Product,
) -> dict[str, dict[int, CommercialPrice]]:
    return {
        channel: standard_prices_by_variant_id(
            product=product,
            channel=channel,
        )
        for channel in CommercialPrice.Channel.values
    }


def _kept_rows(variant_formset) -> list:
    return [
        row
        for row in variant_formset.ordered_forms_by_position
        if not row.cleaned_data.get("delete")
    ]


def _prices_are_complete(variant_formset) -> bool:
    """A variant sold in retail needs a retail price (EUR or SEK), said on
    its card."""

    complete = True

    for row in _kept_rows(variant_formset):
        if not row.cleaned_data.get("retail"):
            continue

        prices = row.prices()

        if prices.retail_eur is not None or prices.retail_sek is not None:
            continue

        complete = False
        row.add_error("retail_eur", "Sold in retail: give it a price.")

    return complete


def _pricing_by_variant_id(
    *,
    product: Product,
    variant_formset,
) -> dict[int, VariantPricing]:
    """Each kept row's channels and prices, by its variant (a new row's by
    its label, now saved)."""

    variant_id_by_label = {
        variant.label.casefold(): variant.pk
        for variant in product.variants.all()
    }
    pricing: dict[int, VariantPricing] = {}

    for row in _kept_rows(variant_formset):
        data = row.cleaned_data
        variant_id = data.get("variant_id") or variant_id_by_label.get(
            " ".join(data["label"].split()).casefold()
        )

        if variant_id is None:
            continue

        pricing[variant_id] = VariantPricing(
            retail_enabled=bool(data.get("retail")),
            business_enabled=bool(data.get("business")),
            prices=row.prices(),
        )

    return pricing


@login_required
def create(request):
    if request.method == "POST":
        form = ProductForm(
            request.POST,
        )

        pricing_form = (
            ProductPricingForm(
                request.POST,
            )
        )

        product_form_is_valid = (
            form.is_valid()
        )
        pricing_form_is_valid = (
            pricing_form.is_valid()
        )

        if (
            product_form_is_valid
            and pricing_form_is_valid
        ):
            try:
                with transaction.atomic():
                    result = create_product(
                        internal_number=(
                            form.cleaned_data[
                                "internal_number"
                            ]
                        ),
                        manufacturer=(
                            form.cleaned_data[
                                "manufacturer"
                            ]
                        ),
                        brand=(
                            form.cleaned_data[
                                "brand"
                            ]
                        ),
                        name=(
                            form.cleaned_data[
                                "name"
                            ]
                        ),
                        weight_per_unit=(
                            form.cleaned_data[
                                "weight_per_unit"
                            ]
                        ),
                        stock_unit=(
                            form.cleaned_data[
                                "stock_unit"
                            ]
                        ),
                        vegan=(
                            form.cleaned_data[
                                "vegan"
                            ]
                        ),
                        user=request.user,
                    )

                    if result.created:
                        (
                            update_product_standard_pricing(
                                product=(
                                    result.item
                                ),
                                **(
                                    pricing_form
                                    .pricing_values()
                                ),
                            )
                        )

            except InvalidProductData as error:
                form.add_error(
                    None,
                    str(error),
                )

            except InvalidCommercialPrice as error:
                pricing_form.add_error(
                    None,
                    str(error),
                )

            else:
                if not result.created:
                    messages.info(
                        request,
                        result.message,
                    )

                    return redirect(
                        "ops_products:index"
                    )

                # A new product goes on to its edit page: its picture and
                # category, then its shop text (its own page).
                messages.success(
                    request,
                    (
                        f"{result.message} "
                        "Now add its picture and category, then its shop text."
                    ),
                )

                return redirect(
                    "ops_products:edit",
                    product_pk=result.item.pk,
                )

    else:
        form = ProductForm()
        pricing_form = (
            ProductPricingForm()
        )

    context = (
        build_create_product_form_context(
            form=form,
            pricing_form=pricing_form,
        )
        .as_dict()
    )

    return render(
        request,
        (
            "ops_portal/products/"
            "product_form.html"
        ),
        context,
    )


@login_required
def edit_catalog(
    request,
    product_pk: int,
):
    """The product's shop text: per language its name, description and
    ingredients (its category and picture are on the product form)."""

    product = _get_product_or_404(
        product_pk
    )

    if request.method == "POST":
        languages = build_catalog_languages(
            product=product,
            data=request.POST,
        )

        if all([language.form.is_valid() for language in languages]):
            try:
                product = update_product_catalog(
                    product=product,
                    texts={
                        language.code: language.form.change()
                        for language in languages
                    },
                    user=request.user,
                )

            except InvalidProductData as error:
                languages[0].form.add_error(None, str(error))

            else:
                messages.success(
                    request,
                    f"Shop text of {product.sku} updated.",
                )

                # Saved, and still here, like the product form.
                return redirect(
                    "ops_products:edit_catalog",
                    product_pk=product.pk,
                )

    else:
        languages = build_catalog_languages(
            product=product,
        )

    context = build_catalog_form_context(
        languages=languages,
        product=product,
    ).as_dict()

    return render(
        request,
        "ops_portal/products/catalog_form.html",
        context,
    )


def _get_product_or_404(
    product_pk: int,
) -> Product:
    return get_object_or_404(
        Product.objects.select_related(
            "profile"
        ),
        pk=product_pk,
    )
