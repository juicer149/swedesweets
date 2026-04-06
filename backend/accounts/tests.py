from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Store

User = get_user_model()


class AccountsViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.store_user = User.objects.create_user(
            username="store@example.com",
            email="store@example.com",
            password="testpass123",
        )
        self.store = Store.objects.create(
            user=self.store_user,
            name="Store One",
            address="Main street 1",
            is_active=True,
        )

        self.staff_user = User.objects.create_user(
            username="staff@example.com",
            email="staff@example.com",
            password="testpass123",
            is_staff=True,
        )

        self.plain_user = User.objects.create_user(
            username="plain@example.com",
            email="plain@example.com",
            password="testpass123",
        )

    def test_portal_requires_login(self):
        response = self.client.get(reverse("accounts:portal"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_portal_redirects_store_user_to_store_portal(self):
        self.client.login(username="store@example.com", password="testpass123")
        response = self.client.get(reverse("accounts:portal"))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("accounts:store_portal"))

    def test_store_portal_renders_for_logged_in_store_user(self):
        self.client.login(username="store@example.com", password="testpass123")
        response = self.client.get(reverse("accounts:store_portal"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["store"], self.store)

    def test_portal_redirects_staff_user_to_staff_portal(self):
        self.client.login(username="staff@example.com", password="testpass123")
        response = self.client.get(reverse("accounts:portal"))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("accounts:staff_portal"))

    def test_staff_portal_renders_for_staff_user(self):
        self.client.login(username="staff@example.com", password="testpass123")
        response = self.client.get(reverse("accounts:staff_portal"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("open_orders", response.context)
        self.assertIn("unprocessed_partner_requests", response.context)

    def test_staff_portal_forbids_store_user(self):
        self.client.login(username="store@example.com", password="testpass123")
        response = self.client.get(reverse("accounts:staff_portal"))

        self.assertEqual(response.status_code, 403)

    def test_portal_returns_fallback_for_plain_user_without_store(self):
        self.client.login(username="plain@example.com", password="testpass123")
        response = self.client.get(reverse("accounts:portal"))

        self.assertEqual(response.status_code, 403)

    def test_store_portal_forbids_plain_user_without_store(self):
        self.client.login(username="plain@example.com", password="testpass123")
        response = self.client.get(reverse("accounts:store_portal"))

        self.assertEqual(response.status_code, 403)

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

        response = self.client.get(reverse("accounts:store_list"))

        self.assertEqual(response.status_code, 200)
        stores = list(response.context["stores"])
        self.assertEqual(len(stores), 1)
        self.assertEqual(stores[0]["name"], "Store One")
