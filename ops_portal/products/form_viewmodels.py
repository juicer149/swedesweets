from __future__ import annotations

from dataclasses import dataclass

from django.urls import reverse

from ops_portal.products.catalog_forms import (
    CatalogForm,
    CatalogLanguage,
)
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


@dataclass(frozen=True, slots=True)
class FormSection:
    """One section of the product form, one under the other on one page
    (no tabs: what belongs together stays in sight)."""

    key: str
    title: str
    template: str


PRODUCT_FORM_SECTIONS = (
    FormSection(
        key="product",
        title="Product",
        template="ops_portal/products/includes/form_section_product.html",
    ),
    FormSection(
        key="pricing",
        title="Pricing",
        template="ops_portal/products/includes/form_section_pricing.html",
    ),
)

# Editing a product adds its Variants last, before the actions (a new
# product starts with one).
PRODUCT_EDIT_FORM_SECTIONS = (
    *PRODUCT_FORM_SECTIONS,
    FormSection(
        key="variants",
        title="Variants",
        template="ops_portal/products/includes/form_section_variants.html",
    ),
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
            "form_sections": (
                PRODUCT_EDIT_FORM_SECTIONS
                if self.variant_formset is not None
                else PRODUCT_FORM_SECTIONS
            ),
            "variant_formset": self.variant_formset,
            "variants_unlocked": self.variants_unlocked,
            "variants_unlocked_field": VARIANTS_UNLOCKED_FIELD,
            "variant_label_suggestions": SUGGESTED_VARIANT_LABELS,
            "variant_label_suggestions_id": LABEL_SUGGESTIONS_ID,
            "status_key": (
                "active" if self.product and self.product.active else "inactive"
            ),
            "status_label": (
                "Active" if self.product and self.product.active else "Inactive"
            ),
            "status_icon": (
                product_status_icon(self.product) if self.product else ""
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


@dataclass(frozen=True, slots=True)
class CatalogFormContext:
    """The catalog form: category and picture, then the words per
    language under language tabs (catalog_form.html)."""

    form: CatalogForm
    languages: tuple[CatalogLanguage, ...]
    product: Product

    def as_dict(self) -> dict[str, object]:
        product = self.product

        return {
            "form": self.form,
            "languages": self.languages,
            "product": product,
            "status_key": "active" if product.active else "inactive",
            "status_label": "Active" if product.active else "Inactive",
            "status_icon": product_status_icon(product),
            "current_image_url": _current_product_image_url(product),
            "title": f"Edit catalog: {product.display_name}",
            "description": "",
            "submit_label": "Update catalog",
            "cancel_url": (
                reverse(
                    "ops_products:detail",
                    kwargs={"product_pk": product.pk},
                )
                + "#catalog"
            ),
        }


def build_catalog_form_context(
    *,
    form: CatalogForm,
    languages: tuple[CatalogLanguage, ...],
    product: Product,
) -> CatalogFormContext:
    return CatalogFormContext(
        form=form,
        languages=languages,
        product=product,
    )


def _current_product_image_url(
    product: Product,
) -> str:
    return product_display_url(getattr(product, "profile", None)) or ""
