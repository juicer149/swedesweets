from __future__ import annotations

from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
)
from django.utils.translation import gettext_lazy as _


class LoginForm(AuthenticationForm):
    """Django's login form, with the field names as placeholders.

    The login page hides its labels visually (they stay for screen readers)
    and lets the placeholders say what goes where.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["placeholder"] = _("Username")
        self.fields["password"].widget.attrs["placeholder"] = _("Password")


class ResetRequestForm(PasswordResetForm):
    """Django's password reset form, with "Email" as the placeholder."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs["placeholder"] = _("Email")


class AccountPasswordChangeForm(PasswordChangeForm):
    """Django's change-password form, each field's label as its placeholder.

    The labels are Django's own (already translated); the page hides them
    visually and keeps them for screen readers.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["placeholder"] = field.label
