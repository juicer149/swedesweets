from django.test import TestCase

from partner_request.forms import PartnerRequestForm
from partner_request.models import PartnerRequest


class PartnerRequestFormTests(TestCase):
    def test_form_normalizes_email(self):
        form = PartnerRequestForm(
            data={
                "name": "Marco",
                "store_name": "Candy Shop",
                "email": "  HELLO@STORE.COM ",
                "phone": "123",
                "address": "Main street 1",
                "message": "Interested",
            }
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["email"], "hello@store.com")

    def test_form_strips_text_fields(self):
        form = PartnerRequestForm(
            data={
                "name": "  Marco  ",
                "store_name": "  Candy Shop  ",
                "email": "hello@store.com",
                "phone": "  123  ",
                "address": "  Main street 1  ",
                "message": "  Interested  ",
            }
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["name"], "Marco")
        self.assertEqual(form.cleaned_data["store_name"], "Candy Shop")
        self.assertEqual(form.cleaned_data["phone"], "123")
        self.assertEqual(form.cleaned_data["address"], "Main street 1")
        self.assertEqual(form.cleaned_data["message"], "Interested")


class PartnerRequestModelTests(TestCase):
    def test_save_normalizes_email_at_persistence_boundary(self):
        request_obj = PartnerRequest.objects.create(
            name="Marco",
            store_name="Candy Shop",
            email="  HELLO@STORE.COM ",
        )

        self.assertEqual(request_obj.email, "hello@store.com")

    def test_mark_processed_sets_processed_fields(self):
        request_obj = PartnerRequest.objects.create(
            name="Marco",
            store_name="Candy Shop",
            email="hello@store.com",
        )

        request_obj.mark_processed()
        request_obj.refresh_from_db()

        self.assertTrue(request_obj.is_processed)
        self.assertIsNotNone(request_obj.processed_at)

    def test_mark_unprocessed_resets_processed_fields(self):
        request_obj = PartnerRequest.objects.create(
            name="Marco",
            store_name="Candy Shop",
            email="hello@store.com",
        )

        request_obj.mark_processed()
        request_obj.mark_unprocessed()
        request_obj.refresh_from_db()

        self.assertFalse(request_obj.is_processed)
        self.assertIsNone(request_obj.processed_at)
