from django import forms

from .models import PartnerRequest


class PartnerRequestForm(forms.ModelForm):
    """
    Public form for partner interest submission.

    DESIGN:
    - Forms are the HTTP/input boundary in Django.
    - The form validates and normalizes user input before persistence.
    - Widgets keep presentation hints close to field definitions without moving
      business rules into templates.
    """

    class Meta:
        model = PartnerRequest
        fields = [
            "name",
            "store_name",
            "email",
            "phone",
            "address",
            "message",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "e.g. Marco Dupont",
                    "autocomplete": "name",
                }
            ),
            "store_name": forms.TextInput(
                attrs={
                    "placeholder": "e.g. Chamonix Candy Shop",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "e.g. hello@store.com",
                    "autocomplete": "email",
                    "required": True,
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "placeholder": "e.g. +33 6 12 34 56 78",
                    "autocomplete": "tel",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "placeholder": "e.g. 12 Rue de la Gare, 74400 Chamonix",
                    "rows": 3,
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "placeholder": "Tell us about your store or interest",
                    "rows": 4,
                }
            ),
        }

    def clean_email(self) -> str:
        email = self.cleaned_data["email"]
        return email.strip().lower()

    def clean_name(self) -> str:
        return self.cleaned_data.get("name", "").strip()

    def clean_store_name(self) -> str:
        return self.cleaned_data.get("store_name", "").strip()

    def clean_phone(self) -> str:
        return self.cleaned_data.get("phone", "").strip()

    def clean_address(self) -> str:
        return self.cleaned_data.get("address", "").strip()

    def clean_message(self) -> str:
        return self.cleaned_data.get("message", "").strip()
