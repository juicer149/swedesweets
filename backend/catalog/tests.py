from django.test import TestCase

from catalog.models import Product, ProductCategory
from catalog.read.selectors import (
    get_product_detail,
    list_orderable_products,
    list_visible_products_grouped_by_category,
)


class CatalogSelectorTests(TestCase):
    def setUp(self):
        self.candy = ProductCategory.objects.create(name="Candy", sort_order=1)
        self.chips = ProductCategory.objects.create(name="Chips", sort_order=2)

        self.visible_and_orderable = Product.objects.create(
            code=1,
            name="Sour Skulls",
            category=self.candy,
            is_visible=True,
            is_orderable=True,
        )
        self.visible_not_orderable = Product.objects.create(
            code=2,
            name="Seasonal Candy",
            category=self.candy,
            is_visible=True,
            is_orderable=False,
        )
        self.hidden_orderable = Product.objects.create(
            code=3,
            name="Internal Product",
            category=self.chips,
            is_visible=False,
            is_orderable=True,
        )

    def test_list_orderable_products_returns_only_orderable_products(self):
        products = list_orderable_products()
        product_ids = {product.id for product in products}

        self.assertIn(self.visible_and_orderable.id, product_ids)
        self.assertIn(self.hidden_orderable.id, product_ids)
        self.assertNotIn(self.visible_not_orderable.id, product_ids)

    def test_list_visible_products_grouped_by_category_returns_only_visible_products(self):
        categories = list_visible_products_grouped_by_category()

        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0].name, "Candy")
        visible_ids = {product.id for product in categories[0].visible_products}
        self.assertIn(self.visible_and_orderable.id, visible_ids)
        self.assertIn(self.visible_not_orderable.id, visible_ids)
        self.assertNotIn(self.hidden_orderable.id, visible_ids)

    def test_get_product_detail_returns_visible_product(self):
        product = get_product_detail(product_id=self.visible_and_orderable.id)
        self.assertEqual(product.id, self.visible_and_orderable.id)

    def test_get_product_detail_404s_for_invisible_product(self):
        with self.assertRaisesMessage(Exception, "No Product matches the given query."):
            get_product_detail(product_id=self.hidden_orderable.id)
