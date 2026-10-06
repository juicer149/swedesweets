from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.tests.factories import (
    customer_user_factory,
    full_staff_user_factory,
    superuser_factory,
)
from customers.tests.factories import customer_factory


@pytest.fixture
def owner_client(client):
    client.force_login(superuser_factory())
    return client


@pytest.fixture
def customer_login():
    customer = customer_factory(name="Café Blanc", email="cafe@example.fr")
    return customer_user_factory(customer=customer, username="login@example.fr")


@pytest.mark.django_db
def test_list_shows_accounts_as_rows_on_phones(owner_client, customer_login):
    response = owner_client.get(reverse("ops_accounts:index"), {"view": "customer"})
    content = response.content.decode()

    assert response.status_code == 200
    (row,) = response.context["account_rows"]
    assert row.email == "login@example.fr"
    assert row.meta.endswith("· Café Blanc")
    assert 'class="lines mobile-lines"' in content
    assert "mobile-card" not in content


@pytest.mark.django_db
def test_customer_login_detail_has_tabs_and_quiet_deactivate(
    owner_client,
    customer_login,
):
    response = owner_client.get(
        reverse("ops_accounts:detail", kwargs={"user_id": customer_login.pk}),
    )
    content = response.content.decode()

    assert response.status_code == 200
    assert response.context["status_key"] == "active"
    assert [tab.key for tab in response.context["page_tabs"]] == [
        "account",
        "activity",
    ]

    deactivate_url = reverse(
        "ops_accounts:deactivate_customer_account",
        kwargs={"user_id": customer_login.pk},
    )
    assert f'href="{deactivate_url}"' in content
    assert "quiet-link--danger" in content
    assert "This account has no recorded activity yet." in content
    assert "Back to accounts" in content


@pytest.mark.django_db
def test_staff_detail_has_edit_account(owner_client):
    staff = full_staff_user_factory(username="staff@example.fr")

    response = owner_client.get(
        reverse("ops_accounts:detail", kwargs={"user_id": staff.pk}),
    )
    content = response.content.decode()

    edit_url = reverse("ops_accounts:edit_internal", kwargs={"user_id": staff.pk})
    assert f'href="{edit_url}"' in content
    assert response.context["status_action"] is None


@pytest.mark.django_db
def test_deactivate_page_is_calm_with_a_red_button(owner_client, customer_login):
    response = owner_client.get(
        reverse(
            "ops_accounts:deactivate_customer_account",
            kwargs={"user_id": customer_login.pk},
        ),
    )
    content = response.content.decode()

    assert response.status_code == 200
    assert "button--tone-danger" in content
    assert "Café Blanc" in content
    assert "form-context-card" not in content


@pytest.mark.django_db
def test_edit_form_has_status_heading_and_create_has_none(owner_client):
    staff = full_staff_user_factory(username="staff@example.fr")

    edit = owner_client.get(
        reverse("ops_accounts:edit_internal", kwargs={"user_id": staff.pk}),
    )
    assert edit.status_code == 200
    assert edit.context["title"] == "Edit staff@example.fr"
    assert "data-dirty-form" in edit.content.decode()

    create = owner_client.get(reverse("ops_accounts:create_internal"))
    assert create.status_code == 200
    assert "status_key" not in create.context
    assert 'class="visually-hidden">Create internal account</h1>' in (
        create.content.decode()
    )
