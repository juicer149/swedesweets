from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from accounts.domain.roles import StaffAccessLevel
from accounts.models import StaffAccount, Store

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

        self.restricted_user = User.objects.create_user(
            username="ops@example.com",
            email="ops@example.com",
            password="testpass123",
            is_staff=False,
            is_superuser=False,
        )
        self.restricted_staff = StaffAccount.objects.create(
            user=self.restricted_user,
            access_level=StaffAccessLevel.RESTRICTED,
        )

        self.full_user = User.objects.create_user(
            username="adminstaff@example.com",
            email="adminstaff@example.com",
            password="testpass123",
            is_staff=True,
            is_superuser=True,
        )
        self.full_staff = StaffAccount.objects.create(
            user=self.full_user,
            access_level=StaffAccessLevel.FULL,
        )

        self.plain_user = User.objects.create_user(
            username="plain@example.com",
            email="plain@example.com",
            password="testpass123",
        )

    def test_portal_redirects_store_user_to_store_portal(self):
        self.client.login(username="store@example.com", password="testpass123")
        response = self.client.get(reverse("accounts:portal"))
        self.assertRedirects(response, reverse("accounts:store_portal"))

    def test_portal_redirects_restricted_staff_to_restricted_staff_portal(self):
        self.client.login(username="ops@example.com", password="testpass123")
        response = self.client.get(reverse("accounts:portal"))
        self.assertRedirects(response, reverse("accounts:restricted_staff_portal"))

    def test_portal_redirects_full_staff_to_staff_portal(self):
        self.client.login(username="adminstaff@example.com", password="testpass123")
        response = self.client.get(reverse("accounts:portal"))
        self.assertRedirects(response, reverse("accounts:staff_portal"))

    def test_plain_user_gets_fallback_page(self):
        self.client.login(username="plain@example.com", password="testpass123")
        response = self.client.get(reverse("accounts:portal"))
        self.assertEqual(response.status_code, 403)

    def test_restricted_staff_cannot_access_full_staff_portal(self):
        self.client.login(username="ops@example.com", password="testpass123")
        response = self.client.get(reverse("accounts:staff_portal"))
        self.assertEqual(response.status_code, 403)

    def test_full_staff_can_access_staff_portal(self):
        self.client.login(username="adminstaff@example.com", password="testpass123")
        response = self.client.get(reverse("accounts:staff_portal"))
        self.assertEqual(response.status_code, 200)

    def test_restricted_staff_can_access_restricted_staff_portal(self):
        self.client.login(username="ops@example.com", password="testpass123")
        response = self.client.get(reverse("accounts:restricted_staff_portal"))
        self.assertEqual(response.status_code, 200)

    def test_restricted_staff_has_no_admin_access_flag(self):
        self.assertFalse(self.restricted_user.is_staff)
        self.assertFalse(self.restricted_user.is_superuser)

    def test_full_staff_has_admin_access_flags(self):
        self.assertTrue(self.full_user.is_staff)
        self.assertTrue(self.full_user.is_superuser)

    def test_full_staff_can_create_restricted_staff_account(self):
        self.client.login(username="adminstaff@example.com", password="testpass123")

        response = self.client.post(
            reverse("accounts:create_staff_account"),
            {
                "username": "newops",
                "email": "newops@example.com",
                "password1": "strong-pass-123",
                "password2": "strong-pass-123",
                "access_level": StaffAccessLevel.RESTRICTED,
            },
        )

        self.assertRedirects(response, reverse("accounts:staff_portal"))
        user = User.objects.get(username="newops")
        staff_account = StaffAccount.objects.get(user=user)

        self.assertEqual(staff_account.access_level, StaffAccessLevel.RESTRICTED)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_full_staff_can_create_store_account(self):
        self.client.login(username="adminstaff@example.com", password="testpass123")

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

        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(store.name, "New Store")

    def test_restricted_staff_cannot_create_accounts(self):
        self.client.login(username="ops@example.com", password="testpass123")
        response = self.client.get(reverse("accounts:account_create_choice"))
        self.assertEqual(response.status_code, 403)
