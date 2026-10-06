from __future__ import annotations

import pytest

from accounts.tests.factories import full_staff_user_factory


@pytest.mark.django_db
def test_404_is_a_calm_page_with_a_way_back(client):
    # Signed in: anonymous visitors to an unknown ops URL go to the login.
    client.force_login(full_staff_user_factory())

    response = client.get("/this-page-does-not-exist/")
    content = response.content.decode()

    assert response.status_code == 404
    assert "error-page__code" in content
    assert "page__submit" in content
    assert "error-card" not in content
