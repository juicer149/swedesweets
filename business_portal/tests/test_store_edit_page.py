from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.tests.factories import customer_user_factory
from customers.tests.factories import customer_factory


@pytest.mark.django_db
def test_store_edit_page_shows_form_and_actions(client):
    client.force_login(
        customer_user_factory(
            customer=customer_factory(email="store@example.com"),
        )
    )

    response = client.get(reverse("business_portal:edit_store"))
    content = response.content.decode()

    assert response.status_code == 200
    assert 'name="email"' in content
    assert 'value="store@example.com"' in content
    assert f'href="{reverse("business_portal:index")}"' in content
