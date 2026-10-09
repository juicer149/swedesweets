"""New accounts are invited by mail to choose their own password; staff
never type one in."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse

from accounts.tests.factories import superuser_factory
from customers.models import Customer
from customers.tests.factories import customer_factory

User = get_user_model()


@pytest.fixture
def owner_client(client):
    client.force_login(superuser_factory())
    return client


@pytest.mark.django_db
@override_settings(SITE_URL="https://www.swedesweets.se")
def test_invite_shop_creates_customer_and_login_and_mails_in_french(
    owner_client,
    mailoutbox,
    django_capture_on_commit_callbacks,
):
    # Name, email and country are enough: the shop fills in the rest.
    with django_capture_on_commit_callbacks(execute=True):
        response = owner_client.post(
            reverse("ops_customers:invite"),
            {"name": "Café Blanc", "email": "Cafe@Example.fr", "country": "FR"},
        )

    customer = Customer.objects.get(email="cafe@example.fr")
    assert response.status_code == 302
    assert response.url == reverse(
        "ops_customers:detail",
        kwargs={"customer_pk": customer.pk},
    )
    assert not customer.is_complete

    user = User.objects.get(email="cafe@example.fr")
    assert not user.has_usable_password()
    assert user.customer_membership.customer == customer

    (mail,) = mailoutbox
    assert mail.to == ["cafe@example.fr"]
    assert "https://www.swedesweets.se/accounts/reset/" in mail.body
    html, _mimetype = mail.alternatives[0]
    assert "https://www.swedesweets.se/accounts/reset/" in html
    assert 'lang="fr"' in html


@pytest.mark.django_db
def test_an_existing_customer_can_be_invited_to_the_portal(
    owner_client,
    mailoutbox,
    django_capture_on_commit_callbacks,
):
    customer = customer_factory(name="Café Blanc", email="cafe@example.fr")

    with django_capture_on_commit_callbacks(execute=True):
        owner_client.post(
            reverse("ops_customers:invite_login", kwargs={"customer_pk": customer.pk}),
            {"email": "second@example.fr"},
        )

    user = User.objects.get(email="second@example.fr")
    assert user.customer_membership.customer == customer
    (mail,) = mailoutbox
    assert mail.to == ["second@example.fr"]


@pytest.mark.django_db
def test_new_internal_account_gets_an_invitation(
    owner_client,
    mailoutbox,
    django_capture_on_commit_callbacks,
):
    with django_capture_on_commit_callbacks(execute=True):
        owner_client.post(
            reverse("ops_accounts:create_internal"),
            {"email": "packer@example.com", "access_level": "restricted"},
        )

    user = User.objects.get(email="packer@example.com")
    assert not user.has_usable_password()

    (mail,) = mailoutbox
    assert mail.to == ["packer@example.com"]
    assert "/accounts/reset/" in mail.body


@pytest.mark.django_db
def test_forgot_password_reaches_an_account_with_no_password_yet(
    client,
    mailoutbox,
):
    # The invitation link expired: "Forgot password?" sends a new one.
    user = User.objects.create_user(
        username="new@example.com",
        email="new@example.com",
    )
    user.set_unusable_password()
    user.save()

    client.post(reverse("password_reset"), {"email": "new@example.com"})

    (mail,) = mailoutbox
    assert mail.to == ["new@example.com"]


@pytest.mark.django_db
def test_invite_shop_refuses_an_email_a_customer_uses(owner_client, mailoutbox):
    customer_factory(name="Café Blanc", email="cafe@example.fr")

    response = owner_client.post(
        reverse("ops_customers:invite"),
        {"name": "Café Noir", "email": "CAFE@example.fr", "country": "FR"},
    )

    assert response.status_code == 200
    errors = response.context["form"].errors["email"]
    assert "Café Blanc already uses this email" in errors[0]
    assert not Customer.objects.filter(name="Café Noir").exists()
    assert mailoutbox == []


@pytest.mark.django_db
def test_invite_shop_refuses_an_email_with_a_login(owner_client, mailoutbox):
    User.objects.create_user(username="staff@example.fr", email="staff@example.fr")

    response = owner_client.post(
        reverse("ops_customers:invite"),
        {"name": "Café Noir", "email": "staff@example.fr", "country": "FR"},
    )

    assert response.status_code == 200
    assert response.context["form"].errors["email"] == [
        "This email already has a login."
    ]
    assert not Customer.objects.filter(name="Café Noir").exists()
    assert mailoutbox == []


@pytest.mark.django_db
def test_invite_login_takes_the_customers_own_email_but_not_a_used_login(
    owner_client,
    mailoutbox,
    django_capture_on_commit_callbacks,
):
    first = customer_factory(name="Café Blanc", email="cafe@example.fr")
    other = customer_factory(name="Café Noir", email="noir@example.fr")
    url = reverse("ops_customers:invite_login", kwargs={"customer_pk": other.pk})

    # Its own customer email is free for a login.
    with django_capture_on_commit_callbacks(execute=True):
        owner_client.post(url, {"email": "noir@example.fr"})
    assert User.objects.filter(email="noir@example.fr").exists()

    # A login that exists already is named on the field.
    first_url = reverse("ops_customers:invite_login", kwargs={"customer_pk": first.pk})
    response = owner_client.post(first_url, {"email": "noir@example.fr"})

    assert response.status_code == 200
    assert response.context["form"].errors["email"] == [
        "This email already has a login, for Café Noir."
    ]
    assert len(mailoutbox) == 1
