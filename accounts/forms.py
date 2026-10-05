from __future__ import annotations

from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
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
