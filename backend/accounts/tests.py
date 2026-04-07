from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from accounts.domain.roles import StaffAccessLevel
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

    def test_account_create_choice_requires_staff(self):
        self.client.login(username="store@example.com", password="testpass123")
        response = self.client.get(reverse("accounts:account_create_choice"))
        self.assertEqual(response.status_code, 403)

    def test_account_create_choice_renders_for_staff(self):
        self.client.login(username="staff@example.com", password="testpass123")
        response = self.client.get(reverse("accounts:account_create_choice"))
        self.assertEqual(response.status_code, 200)

    def test_create_store_account_creates_user_and_store(self):
        self.client.login(username="staff@example.com", password="testpass123")

        response = self.client.post(
            reverse("accounts:create_store_account"),
            {
                "username": "newstore",
                "email": "newstore@example.com",
                "password1": "strong-pass-123",
                "password2": "strong-pass-123",
                "store_name": "New Store",
                "phone": "+33 1 23 45 67 89",
                "address": "12 Rue Example, Paris",
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("accounts:staff_portal"))
        user = User.objects.get(username="newstore")
        store = Store.objects.get(user=user)

        self.assertEqual(user.email, "newstore@example.com")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(store.name, "New Store")
        self.assertTrue(store.is_active)

    def test_create_staff_account_creates_restricted_staff_user(self):
        self.client.login(username="staff@example.com", password="testpass123")

        response = self.client.post(
            reverse("accounts:create_staff_account"),
            {
                "username": "opsuser",
                "email": "ops@example.com",
                "password1": "strong-pass-123",
                "password2": "strong-pass-123",
                "access_level": StaffAccessLevel.RESTRICTED,
            },
        )

        self.assertRedirects(response, reverse("accounts:staff_portal"))
        user = User.objects.get(username="opsuser")

        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(hasattr(user, "store"))

    def test_create_staff_account_creates_full_staff_user(self):
        self.client.login(username="staff@example.com", password="testpass123")

        response = self.client.post(
            reverse("accounts:create_staff_account"),
            {
                "username": "adminuser",
                "email": "adminuser@example.com",
                "password1": "strong-pass-123",
                "password2": "strong-pass-123",
                "access_level": StaffAccessLevel.FULL,
            },
        )

        self.assertRedirects(response, reverse("accounts:staff_portal"))
        user = User.objects.get(username="adminuser")

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_create_store_account_rejects_duplicate_username(self):
        self.client.login(username="staff@example.com", password="testpass123")

        response = self.client.post(
            reverse("accounts:create_store_account"),
            {
                "username": "store@example.com",
                "email": "another@example.com",
                "password1": "strong-pass-123",
                "password2": "strong-pass-123",
                "store_name": "Duplicate Store",
                "phone": "",
                "address": "Some address",
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A user with this username already exists.")

    def test_create_store_account_rejects_password_mismatch(self):
        self.client.login(username="staff@example.com", password="testpass123")

        response = self.client.post(
            reverse("accounts:create_store_account"),
            {
                "username": "anotherstore",
                "email": "anotherstore@example.com",
                "password1": "strong-pass-123",
                "password2": "wrong-pass-123",
                "store_name": "Another Store",
                "phone": "",
                "address": "Some address",
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The two passwords do not match.")
        self.assertFalse(User.objects.filter(username="anotherstore").exists())
