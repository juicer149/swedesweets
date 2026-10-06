from __future__ import annotations

from dataclasses import dataclass

from django.urls import reverse

from accounts.roles import RoleSpec
from common.page_header import PageHeader, PageHeaderAction
from common.table_controls import QuickJumpOption, QuickJumpSearch
from common.ui import (
    StatusPresentation,
)
from ops_portal.products.access import can_create_product
from ops_portal.products.presentation import (
    product_status_icon,
    product_status_presentation,
)
from products.models import Product


@dataclass(frozen=True, slots=True)
class ProductPageRow:
    product: Product
    status: StatusPresentation
    detail_href: str
    weight_label: str
    unit_label: str

    @property
    def meta(self) -> str:
        """Phones: the grey line under the name (code · manufacturer · vegan)."""

        parts = [
            self.product.code_label,
            self.product.manufacturer,
            "Vegan" if self.product.vegan else "",
        ]
        return " · ".join(part for part in parts if part)

    @property
    def icon(self) -> str:
        return product_status_icon(self.product)


def build_products_page_header(*, role_spec: RoleSpec) -> PageHeader:
    return PageHeader(
        title="Products",
        title_id="products-title",
        action=_build_add_product_header_action(role_spec=role_spec),
    )


def _build_add_product_header_action(
    *,
    role_spec: RoleSpec,
) -> PageHeaderAction | None:
    if not can_create_product(role_spec=role_spec):
        return None

    return PageHeaderAction(
        label="Add product",
        href=reverse("ops_products:create"),
        aria_label="Add a new product",
    )


def build_product_page_rows(products: list[Product]) -> list[ProductPageRow]:
    return [_build_product_page_row(product) for product in products]


def _build_product_page_row(product: Product) -> ProductPageRow:
    status = product_status_presentation(product)
    detail_href = _product_detail_href(product)

    return ProductPageRow(
        product=product,
        status=status,
        detail_href=detail_href,
        weight_label=product.weight_label,
        unit_label=product.stock_unit_singular,
    )


def build_product_quick_jump_search(
    rows: list[ProductPageRow],
) -> QuickJumpSearch:
    return QuickJumpSearch(
        title="Find",
        title_id="products-quick-jump-title",
        select_id="products-quick-jump",
        placeholder="Search by code, brand, or name",
        aria_label="Find product",
        options=[
            QuickJumpOption(
                label=row.product.catalog_label,
                url=row.detail_href,
            )
            for row in rows
        ],
    )


def _product_detail_href(product: Product) -> str:
    return reverse("ops_products:detail", kwargs={"product_pk": product.pk})
