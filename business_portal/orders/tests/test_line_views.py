"""Each kind of product line describes itself as a common.lines.LineView,
which includes/ui/line*.html draw. These pin what each line shows."""

from __future__ import annotations

from business_portal.orders.cart_viewmodels import PortalCartLine
from business_portal.orders.detail_viewmodels import PortalOrderContentLine
from business_portal.orders.review_viewmodels import PortalOrderReviewLine
from common.lines import META_OFFER, META_TOTAL, LineMeta
from storefront.cart_viewmodels import RetailCartLine
from storefront.checkout_viewmodels import CheckoutReviewLine


def test_business_cart_line_view_links_and_skips_empty_metas():
    view = PortalCartLine(
        cart_line_id=1,
        product_label="Apple · 5 kg",
        product_url="/my/catalog/7/",
        image_url=None,
        offer_label=None,
        price_label="€12.00",
        quantity=3,
        quantity_url="/q/",
        remove_url="/r/",
    ).view

    assert view.name == "Apple · 5 kg"
    assert view.href == "/my/catalog/7/"
    assert view.metas == (LineMeta(text="€12.00"),)


def test_review_line_view_puts_the_quantity_aside():
    view = PortalOrderReviewLine(
        quantity=3,
        quantity_label="3 units",
        catalog_label="Apple",
        image_url="/media/apple.png",
        offer_label="Short dated",
        price_label="€12.00",
    ).view

    assert view.href is None
    assert view.aside == "3 units"
    assert view.metas[0] == LineMeta(text="Short dated", kind=META_OFFER)


def test_order_line_view_says_when_a_product_left_the_catalog():
    view = PortalOrderContentLine(
        product=None,
        quantity=2,
        quantity_label="2 units",
        unit="unit",
        catalog_label="Apple",
        offer_label=None,
        price_label=None,
        catalog_href=None,
        image_url=None,
    ).view

    assert view.href is None
    assert [meta.text for meta in view.metas] == [
        "Not currently available in the catalog"
    ]


def test_retail_cart_line_view_marks_the_live_total():
    view = RetailCartLine(
        cart_line_id=9,
        product_label="Apple",
        product_url="/shop/7/",
        image_url=None,
        offer_label=None,
        unit_price_label="€2.50",
        line_total_label="€7.50",
        quantity=3,
        quantity_url="/q/",
        remove_url="/r/",
    ).view

    each, total = view.metas
    assert each.text == "€2.50 each"
    assert total == LineMeta(
        text="€7.50",
        kind=META_TOTAL,
        prefix="Total: ",
        total_for=9,
    )
    assert view.aside == "× 3"


def test_checkout_line_view_shows_quantity_times_price_and_the_total():
    view = CheckoutReviewLine(
        product_label="Apple",
        image_url=None,
        quantity=3,
        unit_price_label="€2.50",
        line_total_label="€7.50",
    ).view

    assert [meta.text for meta in view.metas] == ["3 × €2.50"]
    assert view.aside == "€7.50"
