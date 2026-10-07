from __future__ import annotations

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_pages_carry_favicon_and_a_shareable_preview(client):
    html = client.get(reverse("public_site:faq")).content.decode()

    assert 'rel="icon"' in html
    assert "favicon.svg" in html
    assert 'rel="apple-touch-icon"' in html
    assert '<meta property="og:title" content="SwedeSweets">' in html
    # Sharing services need the picture's full address.
    assert 'property="og:image" content="http://testserver/' in html
    assert "og-image" in html
