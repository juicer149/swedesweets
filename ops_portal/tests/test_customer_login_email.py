"""A shop's login gets another address when the shop asks SwedeSweets;
the shop's contact email is a separate thing and stays."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse

from accounts.errors import AccountCreationError
from accounts.services import change_customer_login_email, create_customer_account
from accounts.tests.factories import (
    customer_user_factory,
    superuser_factory,
    user_factory,
)
from customers.tests.factories import customer_factory

User = get_user_model()


@pytest.fixture
def owner_client(client):
    client.force_login(superuser_factory())
    return client


@pytest.fixture
def shop_login():
    customer = customer_factory(name="Café Blanc", email="cafe@example.fr")
    user = customer_user_factory(customer=customer, username="cafe@example.fr")
    return customer, user


@pytest.mark.django_db
def test_change_keeps_the_password_and_the_contact_email(shop_login):
    customer, user = shop_login

    change = change_customer_login_email(user=user, email=" New@Example.fr ")

    user.refresh_from_db()
    customer.refresh_from_db()
    assert change.old_email == "cafe@example.fr"
    assert user.username == "new@example.fr"
    assert user.email == "new@example.fr"
    assert user.check_password("password")
    assert customer.email == "cafe@example.fr"


@pytest.mark.django_db
def test_change_refuses_a_taken_address_and_staff_logins(shop_login):
    _customer, user = shop_login
    staff = user_factory(username="staff@example.fr")

    with pytest.raises(AccountCreationError, match="already exists"):
        change_customer_login_email(user=user, email="STAFF@example.fr")

    with pytest.raises(AccountCreationError, match="not a customer"):
        change_customer_login_email(user=staff, email="other@example.fr")


@pytest.mark.django_db
@override_settings(SITE_URL="https://www.swedesweets.se")
def test_ops_changes_the_login_and_mails_both_addresses_in_french(
    owner_client,
    shop_login,
    mailoutbox,
    django_capture_on_commit_callbacks,
):
    _customer, user = shop_login
    url = reverse("ops_accounts:edit_customer", kwargs={"user_id": user.pk})

    # The account page leads here.
    detail = owner_client.get(
        reverse("ops_accounts:detail", kwargs={"user_id": user.pk})
    )
    assert f'href="{url}"' in detail.content.decode()

    with django_capture_on_commit_callbacks(execute=True):
        response = owner_client.post(url, {"email": "new@example.fr"})

    assert response.status_code == 302
    user.refresh_from_db()
    assert user.email == "new@example.fr"
    assert sorted(mail.to[0] for mail in mailoutbox) == [
        "cafe@example.fr",
        "new@example.fr",
    ]
    html, _mimetype = mailoutbox[0].alternatives[0]
    assert 'lang="fr"' in html
    assert "new@example.fr" in mailoutbox[0].body
    assert "https://www.swedesweets.se/accounts/login/" in mailoutbox[0].body


@pytest.mark.django_db
def test_a_login_without_a_password_gets_the_invitation_again(
    owner_client,
    mailoutbox,
    django_capture_on_commit_callbacks,
):
    # Marco typed the address wrong; the shop never got the invitation.
    customer = customer_factory(name="Café Noir", email="noir@example.fr")
    user = create_customer_account(email="nior@example.fr", customer=customer).user

    with django_capture_on_commit_callbacks(execute=True):
        owner_client.post(
            reverse("ops_accounts:edit_customer", kwargs={"user_id": user.pk}),
            {"email": "noir@example.fr"},
        )

    (mail,) = mailoutbox
    assert mail.to == ["noir@example.fr"]
    assert "/accounts/reset/" in mail.body


@pytest.mark.django_db
def test_a_taken_address_shows_on_the_field(owner_client, shop_login, mailoutbox):
    _customer, user = shop_login
    user_factory(username="taken@example.fr")

    response = owner_client.post(
        reverse("ops_accounts:edit_customer", kwargs={"user_id": user.pk}),
        {"email": "taken@example.fr"},
    )

    assert response.status_code == 200
    assert response.context["form"].errors["email"] == [
        "An account with this email already exists."
    ]
    assert mailoutbox == []


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en")
def test_the_shop_sees_its_login_under_the_contact_email(client, shop_login):
    _customer, user = shop_login
    client.force_login(user)

    content = client.get(reverse("business_portal:edit_store")).content.decode()

    assert "Contact email" in content
    assert "You log in with cafe@example.fr" in content
    assert 'href="mailto:info@swedesweets.se"' in content
