from django import forms
from django.contrib.auth import get_user_model

from accounts.domain.roles import StaffAccessLevel
from accounts.write.commands import CreateStaffAccountCommand, CreateStoreAccountCommand

User = get_user_model()


class BaseAccountCreateForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean_username(self) -> str:
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("A user with this username already exists.")
        return username

    def clean_email(self) -> str:
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two passwords do not match.")

        return cleaned_data


class StoreAccountCreateForm(BaseAccountCreateForm):
    store_name = forms.CharField(max_length=200)
    phone = forms.CharField(max_length=50, required=False)
    address = forms.CharField(widget=forms.Textarea)
    is_active = forms.BooleanField(required=False, initial=True)

    def to_command(self) -> CreateStoreAccountCommand:
        return CreateStoreAccountCommand(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
            store_name=self.cleaned_data["store_name"],
            phone=self.cleaned_data["phone"],
            address=self.cleaned_data["address"],
            is_active=self.cleaned_data["is_active"],
        )


class StaffAccountCreateForm(BaseAccountCreateForm):
    access_level = forms.ChoiceField(
        choices=StaffAccessLevel.choices()
    )

    def clean_access_level(self) -> StaffAccessLevel:
        return StaffAccessLevel(self.cleaned_data["access_level"])

    def to_command(self) -> CreateStaffAccountCommand:
        return CreateStaffAccountCommand(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
            access_level=self.cleaned_data["access_level"],
        )
