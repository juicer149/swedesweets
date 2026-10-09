from __future__ import annotations

from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    _unicode_ci_compare,
)
from django.utils.translation import gettext_lazy as _

UserModel = get_user_model()


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
    """Django's password reset form, with "Email" as the placeholder.

    Unlike Django's, it also reaches accounts that have no password yet:
    a new account is invited to choose one, and if that invitation link
    has expired, "Forgot password?" sends a new one.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs["placeholder"] = _("Email")

    def get_users(self, email):
        email_field_name = UserModel.get_email_field_name()
        active_users = UserModel._default_manager.filter(
            **{
                f"{email_field_name}__iexact": email,
                "is_active": True,
            }
        )
        # As Django's, minus its "has a usable password" condition.
        return (
            user
            for user in active_users
            if _unicode_ci_compare(email, getattr(user, email_field_name))
        )


class _PasswordFormLook:
    """Each field's label as its placeholder, and the password rules for
    the "Your password…" dropdown above the fields.

    The labels are Django's own (already translated); the pages hide them
    visually and keep them for screen readers.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["placeholder"] = field.label

    @property
    def password_rules(self) -> dict[str, object]:
        """{"lead": "Your password", "list": ["must contain …", …]},
        in the current language (computed per request)."""
        lead, items = password_rules()
        return {"lead": lead, "list": items}


class AccountPasswordChangeForm(_PasswordFormLook, PasswordChangeForm):
    """Django's change-password form (My account), in the site's look."""


class AccountSetPasswordForm(_PasswordFormLook, SetPasswordForm):
    """Django's new-password form (the link in the reset mail), in the
    same look as changing the password under My account."""


def split_password_rules(texts: list[str]) -> tuple[str, list[str]]:
    """Pull the words every rule starts with out in front.

    ["Your password must contain …", "Your password can’t be …"] becomes
    ("Your password", ["must contain …", "can’t be …"]). Works in any
    language because it compares words, not a fixed phrase. With fewer
    than two rules, or nothing in common, the lead is empty.
    """
    if len(texts) < 2:
        return "", list(texts)

    split = [text.split(" ") for text in texts]
    common = 0
    for words in zip(*split, strict=False):
        if len(set(words)) != 1:
            break
        common += 1

    # Keep at least one word in every rule.
    common = min(common, min(len(words) for words in split) - 1)
    if common <= 0:
        return "", list(texts)

    lead = " ".join(split[0][:common])
    return lead, [" ".join(words[common:]) for words in split]


def password_rules() -> tuple[str, list[str]]:
    """The configured password rules, split into a lead and the rules."""
    return split_password_rules(
        [str(text) for text in password_validation.password_validators_help_texts()]
    )
