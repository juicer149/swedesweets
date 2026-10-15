"""The password once more (accounts/password_again.py): right, wrong, and
locked after too many wrong ones."""

from __future__ import annotations

import pytest

from accounts.password_again import PasswordAgainForm, is_locked
from accounts.tests.factories import user_factory


def _try(user, password: str) -> PasswordAgainForm:
    form = PasswordAgainForm({"password_again": password}, user=user)
    form.confirmed = form.is_confirmed()

    return form


pytestmark = pytest.mark.usefixtures("fast_password_hashing")

@pytest.mark.django_db
def test_the_right_password_confirms():
    user = user_factory()

    assert _try(user, "password").confirmed is True


@pytest.mark.django_db
def test_no_password_yet_says_nothing():
    user = user_factory()
    form = _try(user, "")

    assert form.confirmed is False
    assert not form.errors


@pytest.mark.django_db
def test_a_wrong_password_says_how_many_tries_are_left(settings):
    settings.PASSWORD_AGAIN_MAX_ATTEMPTS = 3
    user = user_factory()

    form = _try(user, "wrong")

    assert form.confirmed is False
    assert "2 tries left" in str(form.errors)


@pytest.mark.django_db
def test_too_many_wrong_passwords_lock_even_the_right_one(settings):
    settings.PASSWORD_AGAIN_MAX_ATTEMPTS = 3
    user = user_factory()

    for _ in range(3):
        _try(user, "wrong")

    form = _try(user, "password")

    assert is_locked(user)
    assert form.confirmed is False
    assert "Too many wrong passwords" in str(form.errors)


@pytest.mark.django_db
def test_the_right_password_clears_the_count(settings):
    settings.PASSWORD_AGAIN_MAX_ATTEMPTS = 3
    user = user_factory()

    _try(user, "wrong")
    _try(user, "wrong")
    assert _try(user, "password").confirmed is True

    # Counting starts over.
    assert "2 tries left" in str(_try(user, "wrong").errors)


@pytest.mark.django_db
def test_each_user_counts_on_their_own(settings):
    settings.PASSWORD_AGAIN_MAX_ATTEMPTS = 1
    locked = user_factory(username="locked@example.com")
    other = user_factory(username="other@example.com")

    _try(locked, "wrong")

    assert is_locked(locked)
    assert _try(other, "password").confirmed is True
