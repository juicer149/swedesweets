from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from accounts.models import Store
from catalog.models import Product, ProductCategory
from ordering.domain.errors import EmptyOrder, InvalidProductSelection, InvalidQuantity
from ordering.domain.value_objects import BoxQuantity, MAX_BOXES_PER_LINE
from ordering.models import Order, OrderItem
from ordering.read.selectors import (
    get_order_for_store,
    list_active_orders_for_store,
    list_store_orders,
)
from ordering.write.actions import place_order
from ordering.write.commands import PlaceOrderCommand, PlaceOrderLine
from ordering.write.parsing import empty_order_form, parse_order_form

User = get_user_model()


class BoxQuantityTests(SimpleTestCase):
    def test_accepts_positive_integer_within_limit(self):
        quantity = BoxQuantity(3)
        self.assertEqual(quantity.value, 3)

    def test_rejects_zero(self):
        with self.assertRaises(InvalidQuantity):
            BoxQuantity(0)

    def test_rejects_negative_value(self):
        with self.assertRaises(InvalidQuantity):
            BoxQuantity(-1)

    def test_rejects_values_above_max(self):
        with self.assertRaises(InvalidQuantity):
            BoxQuantity(MAX_BOXES_PER_LINE + 1)


class OrderFormParsingTests(TestCase):
    def setUp(self):
        self.category = ProductCategory.objects.create(name="Candy", sort_order=1)
        self.product_1 = Product.objects.create(
            code=1,
            name="Sour Skulls",
            category=self.category,
            is_visible=True,
            is_orderable=True,
        )
        self.product_2 = Product.objects.create(
            code=2,
            name="Salt Chips",
            category=self.category,
            is_visible=True,
            is_orderable=True,
        )

    def test_empty_order_form_contains_all_products_as_rows(self):
        form = empty_order_form([self.product_1, self.product_2])

        self.assertEqual(len(form.rows), 2)
        self.assertEqual(form.lines, ())
        self.assertEqual(form.errors, ())

    def test_parse_order_form_builds_lines_for_positive_box_counts(self):
        form = parse_order_form(
            [self.product_1, self.product_2],
            {
                f"qty_{self.product_1.id}": "3",
                f"qty_{self.product_2.id}": "",
            },
        )

        self.assertTrue(form.is_valid)
        self.assertEqual(len(form.lines), 1)
        self.assertEqual(form.lines[0].product_id, self.product_1.id)
        self.assertEqual(form.lines[0].boxes, 3)

    def test_parse_order_form_rejects_non_integer_boxes(self):
        form = parse_order_form(
            [self.product_1],
            {f"qty_{self.product_1.id}": "abc"},
        )

        self.assertFalse(form.is_valid)
        self.assertIn("whole number", form.errors[0])

    def test_parse_order_form_rejects_negative_boxes(self):
        form = parse_order_form(
            [self.product_1],
            {f"qty_{self.product_1.id}": "-2"},
        )

        self.assertFalse(form.is_valid)
        self.assertIn("cannot be negative", form.errors[0])

    def test_parse_order_form_rejects_too_many_boxes(self):
        form = parse_order_form(
            [self.product_1],
            {f"qty_{self.product_1.id}": str(MAX_BOXES_PER_LINE + 1)},
        )

        self.assertFalse(form.is_valid)
        self.assertIn("cannot exceed", form.errors[0])

    def test_parse_order_form_requires_at_least_one_line(self):
        form = parse_order_form(
            [self.product_1, self.product_2],
            {
                f"qty_{self.product_1.id}": "",
                f"qty_{self.product_2.id}": "0",
            },
        )

        self.assertFalse(form.is_valid)
        self.assertEqual(len(form.errors), 1)
        self.assertIn("greater than zero", form.errors[0])


class PlaceOrderActionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="store@example.com",
            email="store@example.com",
            password="testpass123",
        )
        self.store = Store.objects.create(
            user=self.user,
            name="Test Store",
            phone="123",
            address="Main street 1",
            is_active=True,
        )
        self.category = ProductCategory.objects.create(name="Candy", sort_order=1)
        self.product = Product.objects.create(
            code=10,
            name="Sour Skulls",
            category=self.category,
            weight_grams=1200,
            units_per_box=None,
            is_visible=True,
            is_orderable=True,
        )

    def test_place_order_creates_order_and_snapshots_product_data(self):
        command = PlaceOrderCommand(
            store_id=self.store.id,
            lines=(
                PlaceOrderLine(product_id=self.product.id, boxes=4),
            ),
        )

        result = place_order(command)

        self.assertEqual(result.line_count, 1)
        order = Order.objects.get(pk=result.order_id)
        item = order.items.get()

        self.assertEqual(order.store, self.store)
        self.assertEqual(order.status, Order.Status.PENDING)

        self.assertEqual(item.product_code, self.product.code)
        self.assertEqual(item.product_name, self.product.name)
        self.assertEqual(item.product_category_name, self.category.name)
        self.assertEqual(item.product_weight_grams, 1200)
        self.assertIsNone(item.product_units_per_box)
        self.assertEqual(item.boxes, 4)

    def test_place_order_rejects_empty_order(self):
        command = PlaceOrderCommand(store_id=self.store.id, lines=())

        with self.assertRaises(EmptyOrder):
            place_order(command)

    def test_place_order_rejects_non_orderable_product(self):
        self.product.is_orderable = False
        self.product.save(update_fields=["is_orderable"])

        command = PlaceOrderCommand(
            store_id=self.store.id,
            lines=(
                PlaceOrderLine(product_id=self.product.id, boxes=2),
            ),
        )

        with self.assertRaises(InvalidProductSelection):
            place_order(command)

    def test_place_order_rejects_inactive_store(self):
        self.store.is_active = False
        self.store.save(update_fields=["is_active"])

        command = PlaceOrderCommand(
            store_id=self.store.id,
            lines=(
                PlaceOrderLine(product_id=self.product.id, boxes=2),
            ),
        )

        with self.assertRaisesMessage(Exception, "Inactive stores cannot place orders."):
            place_order(command)


class OrderingReadSelectorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="store2@example.com",
            email="store2@example.com",
            password="testpass123",
        )
        self.store = Store.objects.create(
            user=self.user,
            name="Selector Store",
            address="Street 2",
            is_active=True,
        )
        self.order = Order.objects.create(store=self.store, status=Order.Status.PENDING)
        OrderItem.objects.create(
            order=self.order,
            product_code=1,
            product_name="Product A",
            product_category_name="Candy",
            product_weight_grams=100,
            product_units_per_box=12,
            boxes=3,
        )
        OrderItem.objects.create(
            order=self.order,
            product_code=2,
            product_name="Product B",
            product_category_name="Candy",
            product_weight_grams=200,
            product_units_per_box=24,
            boxes=2,
        )

    def test_list_store_orders_annotates_line_count_and_total_boxes(self):
        orders = list_store_orders(self.store)
        order = orders.get(pk=self.order.pk)

        self.assertEqual(order.line_count, 2)
        self.assertEqual(order.total_boxes, 5)

    def test_list_active_orders_for_store_excludes_delivered_orders(self):
        packed_order = Order.objects.create(
            store=self.store,
            status=Order.Status.PACKED,
        )
        delivered_order = Order.objects.create(
            store=self.store,
            status=Order.Status.DELIVERED,
        )

        active_orders = list_active_orders_for_store(self.store)

        self.assertIn(self.order, active_orders)
        self.assertIn(packed_order, active_orders)
        self.assertNotIn(delivered_order, active_orders)

    def test_get_order_for_store_returns_only_store_order(self):
        fetched = get_order_for_store(self.store, self.order.id)
        self.assertEqual(fetched.id, self.order.id)
        self.assertEqual(fetched.line_count, 2)
        self.assertEqual(fetched.total_boxes, 5)
