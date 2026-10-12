"""Asking for the password again before something that matters.

A page that wants a second look (ops price changes, for one) comes back
with PasswordAgainForm in a dialog
(templates/includes/ui/password_again_dialog.html, js/password_again.js),
and goes on only once `is_confirmed()`.

Wrong passwords are counted per user: after
settings.PASSWORD_AGAIN_MAX_ATTEMPTS (5) within
settings.PASSWORD_AGAIN_LOCK_MINUTES (15), every try is refused (even the
right password) until those minutes have passed since the first wrong
one. A right password clears the count. The count lives in the default
cache, so with an in-memory cache each server process counts on its own.
"""

from __future__ import annotations

from django import forms
from django.conf import settings
from django.core.cache import cache

FIELD_NAME = "password_again"


def max_attempts() -> int:
    return getattr(settings, "PASSWORD_AGAIN_MAX_ATTEMPTS", 5)


def lock_minutes() -> int:
    return getattr(settings, "PASSWORD_AGAIN_LOCK_MINUTES", 15)


def _failures_key(user) -> str:
    return f"password-again:failures:{user.pk}"


def wrong_passwords(user) -> int:
    return cache.get(_failures_key(user), 0)


def is_locked(user) -> bool:
    return wrong_passwords(user) >= max_attempts()


def _count_wrong_password(user) -> None:
    key = _failures_key(user)
    # The window starts at the first wrong password; later ones count
    # within it without moving it.
    cache.add(key, 0, timeout=lock_minutes() * 60)
    cache.incr(key)


def _clear_wrong_passwords(user) -> None:
    cache.delete(_failures_key(user))


class PasswordAgainForm(forms.Form):
    """The user's password, once more."""

    password_again = forms.CharField(
        required=False,
        strip=False,
        label="Your password",
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password"},
        ),
    )

    def __init__(self, *args, user, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.user = user

    def is_confirmed(self) -> bool:
        """Given, right and not locked; a wrong one or the lock is said on
        the field. Not given: not confirmed, nothing said (the dialog has
        only just opened)."""

        if not self.is_valid():
            return False

        password = self.cleaned_data[FIELD_NAME]

        if is_locked(self.user):
            self._say_locked()
            return False

        if not password:
            return False

        if self.user.check_password(password):
            _clear_wrong_passwords(self.user)
            return True

        _count_wrong_password(self.user)

        if is_locked(self.user):
            self._say_locked()
        else:
            left = max_attempts() - wrong_passwords(self.user)
            self.add_error(
                FIELD_NAME,
                f"That is not your password ({left} "
                f"{'try' if left == 1 else 'tries'} left).",
            )

        return False

    def _say_locked(self) -> None:
        self.add_error(
            FIELD_NAME,
            f"Too many wrong passwords: try again in {lock_minutes()} "
            "minutes.",
        )
