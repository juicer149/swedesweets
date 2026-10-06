from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.tests.factories import (
    full_staff_user_factory,
    restricted_staff_user_factory,
)


@pytest.mark.django_db
def test_dashboard_renders_title_queue_section_and_actions(client):
    client.force_login(full_staff_user_factory())

    response = client.get(reverse("ops_dashboard"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Ops dashboard" in content
    assert 'id="dashboard-queue"' in content
    assert "data-async-list" in content
    assert f'href="{reverse("ops_orders:create")}"' in content
    assert f'href="{reverse("ops_inventory:create")}"' in content


@pytest.mark.django_db
def test_dashboard_for_restricted_staff_has_only_add_batch(client):
    client.force_login(restricted_staff_user_factory())

    response = client.get(reverse("ops_dashboard"))
    content = response.content.decode()

    assert response.status_code == 200
    assert f'href="{reverse("ops_orders:create")}"' not in content
    assert f'href="{reverse("ops_inventory:create")}"' in content
