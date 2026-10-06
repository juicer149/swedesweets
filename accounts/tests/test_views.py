from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.tests.factories import (
    customer_user_factory,
)
from customers.tests.factories import (
    customer_factory,
)


@pytest.mark.django_db
def test_business_customer_is_redirected_from_generic_account_page(
    client,
):
    customer = customer_factory()
    user = customer_user_factory(
        customer=customer,
    )

    client.force_login(
        user
    )

    response = client.get(
        reverse("accounts:me")
    )

    assert response.status_code == 302
    assert response["Location"] == reverse(
        "business_portal:index"
    )


@pytest.mark.django_db
def test_my_account_is_calm_with_tabs_and_change_password(client):
    from accounts.tests.factories import full_staff_user_factory

    user = full_staff_user_factory(username="me@example.fr")
    client.force_login(user)

    response = client.get(reverse("accounts:me"))
    content = response.content.decode()

    assert response.status_code == 200
    assert response.context["title"] == "me@example.fr"
    assert [tab.key for tab in response.context["page_tabs"]] == [
        "account",
        "activity",
    ]
    assert f'href="{reverse("password_change")}"' in content
    assert "content-card" not in content
