from __future__ import annotations

import pytest


@pytest.mark.django_db
def test_404_is_a_calm_page_with_a_way_back(client):
    response = client.get("/this-page-does-not-exist/")
    content = response.content.decode()

    assert response.status_code == 404
    assert "error-page__code" in content
    assert "page__submit" in content
    assert "error-card" not in content
