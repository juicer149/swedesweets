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
    # The answered questions, and "Still have questions?" with the contact.
    assert html.count('data-smooth-group="faq"') == len(answered(PUBLIC_FAQ)) + 1



@pytest.mark.django_db
def test_contact_is_the_last_question(client):
    html = client.get(reverse("public_site:faq")).content.decode()

    contact = html.index('id="contact"')
    assert html.rindex('data-smooth-group="faq"') > contact
    # The reseller answer lists the mail too; this is the one after it.
    assert html.index('href="mailto:info@swedesweets.se"', contact) > contact
    assert 'href="tel:+46739756195"' in html


@pytest.mark.django_db
def test_reseller_answer_lists_how_to_reach_us(client):
    html = client.get(reverse("public_site:faq")).content.decode()

    assert "contact page" not in html
    # Under the reseller answer, before "Still have questions?" (which, and
    # the footer, have it too).
    before_last_question = html[: html.index('id="contact"')]
    assert 'href="mailto:info@swedesweets.se"' in before_last_question


@pytest.mark.django_db
def test_shop_answer_links_to_find_sweets(client):
    html = client.get(reverse("public_site:faq")).content.decode()

    assert f'href="{reverse("public_site:find_sweets")}"' in html


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en")
def test_about_page_tells_who_we_are(client):
    response = client.get(reverse("public_site:about"), HTTP_ACCEPT_LANGUAGE="en")
    html = response.content.decode()

    assert response.status_code == 200
    assert "Who we are" in html
    assert "Marco Sandelgård" in html
    assert f'href="{reverse("public_site:about")}"' in html  # the footer link


@pytest.mark.django_db
def test_footer_links_the_faq_and_their_instagram(client):
    html = client.get(reverse("public_site:about")).content.decode()

    footer = html[html.index("site-footer"):]
    assert f'href="{reverse("public_site:faq")}"' in footer
    assert 'href="https://www.instagram.com/swede_sweets/"' in footer
