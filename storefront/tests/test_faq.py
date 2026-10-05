from __future__ import annotations

import pytest
from django.test import override_settings
from django.urls import reverse

from storefront.faq import BUSINESS_FAQ, PUBLIC_FAQ, FaqItem, answered


def test_answered_keeps_order_and_drops_unanswered_questions():
    items = (FaqItem("A?", "a"), FaqItem("B?"), FaqItem("C?", "c"))

    assert [item.question for item in answered(items)] == ["A?", "C?"]


def test_every_faq_list_has_answered_questions():
    assert answered(PUBLIC_FAQ)
    assert answered(BUSINESS_FAQ)


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en")
def test_public_faq_shows_only_answered_questions(client):
    response = client.get(reverse("public_site:faq"), HTTP_ACCEPT_LANGUAGE="en")

    assert response.status_code == 200
    html = response.content.decode()
    for item in PUBLIC_FAQ:
        if item.answer is None:
            assert str(item.question) not in html
        else:
            assert str(item.question) in html
    assert html.count('data-smooth-group="faq"') == len(answered(PUBLIC_FAQ))
