from __future__ import annotations

from django.contrib.auth import password_validation
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

    @property
    def password_rules(self) -> dict[str, object]:
        """{"lead": "Your password", "list": ["must contain …", …]},
        in the current language (computed per request)."""
        lead, items = password_rules()
        return {"lead": lead, "list": items}


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
    for words in zip(*split):
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
