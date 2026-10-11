from __future__ import annotations

from dataclasses import dataclass

from django.urls import reverse

from common.page_tabs import PageTab
from ops_portal.products.forms import (
    ProductEditForm,
    ProductForm,
)
from ops_portal.products.presentation import product_status_icon
from ops_portal.products.pricing_forms import (
    ProductPricingForm,
)
from ops_portal.products.variant_forms import (
    LABEL_SUGGESTIONS_ID,
    SUGGESTED_VARIANT_LABELS,
    VARIANTS_UNLOCKED_FIELD,
    BaseVariantFormSet,
)
from products.images import product_display_url
from products.models import Product

PRODUCT_FORM_TABS = (
    PageTab(
        key="product",
        label="Product",
        icon="lollipop",
        template="ops_portal/products/includes/form_tab_product.html",
    ),
    PageTab(
        key="catalog",
        label="Catalog",
        icon="image",
        template="ops_portal/products/includes/form_tab_catalog.html",
    ),
    PageTab(
        key="pricing",
        label="Pricing",
        icon="tag",
        template="ops_portal/products/includes/form_tab_pricing.html",
    ),
)

# Editing a product adds its Variants (a new product starts with one).
PRODUCT_EDIT_FORM_TABS = (
    PRODUCT_FORM_TABS[0],
    PageTab(
        key="variants",
        label="Variants",
        icon="variants",
        template="ops_portal/products/includes/form_tab_variants.html",
    ),
    *PRODUCT_FORM_TABS[1:],
)


@dataclass(frozen=True, slots=True)
class ProductFormContext:
    form: (
        ProductForm
        | ProductEditForm
    )
    pricing_form: ProductPricingForm
    title: str
    description: str
    submit_label: str
    cancel_url: str
    product: Product | None = None
    current_image_url: str = ""
    variant_formset: BaseVariantFormSet | None = None
    variants_unlocked: bool = False

    def as_dict(
        self,
    ) -> dict[str, object]:
        return {
            "form": self.form,
            "pricing_form": (
                self.pricing_form
            ),
            "product": self.product,
            "page_tabs": (
                PRODUCT_EDIT_FORM_TABS
                if self.variant_formset is not None
                else PRODUCT_FORM_TABS
            ),
            "variant_formset": self.variant_formset,
            "variants_unlocked": self.variants_unlocked,
            "variants_unlocked_field": VARIANTS_UNLOCKED_FIELD,
            "variant_label_suggestions": SUGGESTED_VARIANT_LABELS,
            "variant_label_suggestions_id": LABEL_SUGGESTIONS_ID,
            "tabs_label": "Product form sections",
            "status_key": (
                "active" if self.product and self.product.active else "inactive"
            ),
            "status_label": (
                "Active" if self.product and self.product.active else "Inactive"
            ),
            "status_icon": (
                product_status_icon(self.product) if self.product else ""
            ),
            "current_image_url": (
                self.current_image_url
            ),
            "title": self.title,
            "description": (
                self.description
            ),
            "submit_label": (
                self.submit_label
            ),
            "cancel_url": (
                self.cancel_url
            ),
        }


def build_create_product_form_context(
    *,
    form: ProductForm,
    pricing_form: ProductPricingForm,
) -> ProductFormContext:
    return ProductFormContext(
        form=form,
        pricing_form=pricing_form,
        title="Add product",
        description="",
        submit_label="Add product",
        cancel_url=reverse(
            "ops_products:index"
        ),
    )


def build_edit_product_form_context(
    *,
    form: ProductEditForm,
    pricing_form: ProductPricingForm,
    product: Product,
    variant_formset: BaseVariantFormSet | None = None,
    variants_unlocked: bool = False,
) -> ProductFormContext:
    return ProductFormContext(
        form=form,
        pricing_form=pricing_form,
        product=product,
        variant_formset=variant_formset,
        variants_unlocked=variants_unlocked,
        current_image_url=(
            _current_product_image_url(
                product
            )
        ),
        title=f"Edit {product.display_name}",
        description="",
        submit_label="Update product",
        cancel_url=reverse(
            "ops_products:detail",
            kwargs={
                "product_pk": (
                    product.pk
                ),
            },
        ),
    )


def _current_product_image_url(
    product: Product,
) -> str:
    return product_display_url(getattr(product, "profile", None)) or ""
