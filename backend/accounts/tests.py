from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Store

User = get_user_model()


class AccountsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="store@example.com",
            email="store@example.com",
            password="testpass123",
        )
        self.store = Store.objects.create(
            user=self.user,
            name="Store One",
            address="Main street 1",
            is_active=True,
        )

    def test_portal_requires_login(self):
        response = self.client.get(reverse("portal"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_portal_renders_for_logged_in_store_user(self):
        self.client.login(username="store@example.com", password="testpass123")
        response = self.client.get(reverse("portal"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["store"], self.store)

    def test_store_list_shows_only_active_stores_with_address(self):
        hidden_user = User.objects.create_user(
            username="hidden@example.com",
            email="hidden@example.com",
            password="testpass123",
        )
        Store.objects.create(
            user=hidden_user,
            name="Inactive Store",
            address="Other street 2",
            is_active=False,
        )

        no_address_user = User.objects.create_user(
            username="noaddr@example.com",
            email="noaddr@example.com",
            password="testpass123",
        )
        Store.objects.create(
            user=no_address_user,
            name="No Address Store",
            address="",
            is_active=True,
        )

        response = self.client.get(reverse("store_list"))

        self.assertEqual(response.status_code, 200)
        stores = list(response.context["stores"])
        self.assertEqual(len(stores), 1)
        self.assertEqual(stores[0]["name"], "Store One")
