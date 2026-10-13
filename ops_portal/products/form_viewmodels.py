from __future__ import annotations

from dataclasses import dataclass

from django.urls import reverse

from ops_portal.products.catalog_forms import CatalogLanguage
from ops_portal.products.forms import (
    ProductEditForm,
    ProductForm,
)
from ops_portal.products.price_check import PriceCheck
from ops_portal.products.pricing_forms import (
    ProductPricingForm,
)
from ops_portal.products.variant_forms import (
    LABEL_SUGGESTIONS_ID,
    SUGGESTED_VARIANT_LABELS,
    BaseVariantFormSet,
)
from products.images import product_image_url
from products.models import Product


@dataclass(frozen=True, slots=True)
class FormSection:
    """One section of the product form, one under the other on one page,
    all open (no tabs, no folding: what belongs together stays in sight)."""

    key: str
    title: str
    template: str
    # A "?" beside the title opening this template's explanations
    # (includes/ui/help.html).
    help: str = ""


PRODUCT_SECTION = FormSection(
    key="product",
    title="Product",
    template="ops_portal/products/includes/form_section_product.html",
    help="ops_portal/products/help/product.html",
)

# A new product: its data, then its prices (it has one variant).
PRODUCT_FORM_SECTIONS = (
    PRODUCT_SECTION,
    FormSection(
        key="pricing",
        title="Offers",
        template="ops_portal/products/includes/form_section_pricing.html",
    ),
)

# Editing: the product's data, then its variants with their offers.
PRODUCT_EDIT_FORM_SECTIONS = (
    PRODUCT_SECTION,
    FormSection(
        key="variants",
        title="Variants and offers",
        template="ops_portal/products/includes/form_section_variants.html",
        help="ops_portal/products/help/variants.html",
    ),
)


@dataclass(frozen=True, slots=True)
class ProductFormContext:
    form: (
        ProductForm
        | ProductEditForm
    )
    title: str
    description: str
    submit_label: str
    cancel_url: str
    pricing_form: ProductPricingForm | None = None
    product: Product | None = None
    variant_formset: BaseVariantFormSet | None = None
    # Price changes waiting for the password (price_check.py).
    price_check: PriceCheck | None = None

    def as_dict(
        self,
    ) -> dict[str, object]:
        return {
            "form": self.form,
            "pricing_form": (
                self.pricing_form
            ),
            "price_check": self.price_check,
            "product": self.product,
            "form_sections": (
                PRODUCT_EDIT_FORM_SECTIONS
                if self.variant_formset is not None
                else PRODUCT_FORM_SECTIONS
            ),
            "variant_formset": self.variant_formset,
            "variant_label_suggestions": SUGGESTED_VARIANT_LABELS,
            "variant_label_suggestions_id": LABEL_SUGGESTIONS_ID,
            "title": self.title,
            # Its picture in the Product card (form_section_product.html).
            "heading_image_url": (
                product_image_url(self.product) or "" if self.product else ""
            ),
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
    product: Product,
    variant_formset: BaseVariantFormSet,
    price_check: PriceCheck | None = None,
) -> ProductFormContext:
    return ProductFormContext(
        form=form,
        product=product,
        variant_formset=variant_formset,
        price_check=price_check,
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
    """The shop text form: the name, description and ingredients under one
    tab per language (catalog_form.html)."""

    languages: tuple[CatalogLanguage, ...]
    product: Product

    def as_dict(self) -> dict[str, object]:
        product = self.product

        return {
            "languages": self.languages,
            "product": product,
            # No hero (catalog_form.html): the hidden title names it.
            "title": f"Edit shop text: {product.display_name}",
            "description": "",
            "submit_label": "Update shop text",
            "cancel_url": (
                reverse(
                    "ops_products:detail",
                    kwargs={"product_pk": product.pk},
                )
                + "#text"
            ),
        }


def build_catalog_form_context(
    *,
    languages: tuple[CatalogLanguage, ...],
    product: Product,
) -> CatalogFormContext:
    return CatalogFormContext(
        languages=languages,
        product=product,
    )
