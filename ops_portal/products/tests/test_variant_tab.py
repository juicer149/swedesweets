"""The Variants tab of an ops product: listed on the product page, and
changed from the edit form behind its lock."""

from __future__ import annotations

import pytest
from django.forms import CheckboxInput, FileInput
from django.urls import reverse

from accounts.tests.factories import full_staff_user_factory
from inventory.tests.conftest import TODAY
from inventory.tests.factories import batch_factory
from ops_portal.products.variant_forms import VARIANTS_UNLOCKED_FIELD
from products.tests.factories import product_factory, variant_factory


def _detail_url(product):
    return reverse("ops_products:detail", kwargs={"product_pk": product.pk})


def _edit_url(product):
    return reverse("ops_products:edit", kwargs={"product_pk": product.pk})


def _form_values(form) -> dict[str, str]:
    """What the browser would send for a form as the page drew it."""

    data: dict[str, str] = {}

    for field in form:
        widget = field.field.widget
        value = field.value()

        if isinstance(widget, FileInput):
            continue

        if isinstance(widget, CheckboxInput):
            if value:
                data[field.html_name] = "on"
            continue

        data[field.html_name] = "" if value is None else str(value)

    return data


def _page_post_data(response) -> dict[str, str]:
    context = response.context
    formset = context["variant_formset"]

    data = {
        **_form_values(context["form"]),
        **_form_values(context["pricing_form"]),
        **_form_values(formset.management_form),
    }

    for row in formset:
        data |= _form_values(row)

    return data


@pytest.mark.django_db
def test_the_product_page_lists_its_variants_with_their_stock(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Hoodie", internal_number=601)
    medium = variant_factory(product=product, label="M", first_label="S")
    batch_factory(
        product=product,
        variant=product.variants.get(label="S"),
        today=TODAY,
        batch_id="H-1",
        quantity=4,
    )
    medium.active = False
    medium.save(update_fields=["active"])

    response = client.get(_detail_url(product))
    lines = response.context["variant_lines"]

    assert [line.name for line in lines] == ["S", "M"]
    # S has the batch; M has none.
    assert [line.aside for line in lines] == ["4 boxes", "0 boxes"]
    assert "Paused" in [meta.text for meta in lines[1].metas]
    assert f'href="{_edit_url(product)}#variants"' in response.content.decode()


@pytest.mark.django_db
def test_a_product_with_one_variant_shows_it_as_one(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Apple", internal_number=602)

    response = client.get(_detail_url(product))

    assert [line.name for line in response.context["variant_lines"]] == [
        "One variant",
    ]


@pytest.mark.django_db
def test_the_locked_tab_changes_nothing(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Apple", internal_number=603)

    page = client.get(_edit_url(product))
    data = _page_post_data(page)
    data["variants-0-label"] = "Should not stick"

    response = client.post(_edit_url(product), data)

    assert response.status_code == 302
    assert product.variants.get().label == ""


@pytest.mark.django_db
def test_opening_the_lock_adds_a_variant_and_names_the_first(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Hoodie", internal_number=604)

    page = client.get(_edit_url(product))
    data = _page_post_data(page)
    data |= {
        VARIANTS_UNLOCKED_FIELD: "1",
        "variants-TOTAL_FORMS": "2",
        "variants-0-label": "M",
        "variants-0-position": "2",
        "variants-1-label": "S",
        "variants-1-position": "1",
        "variants-1-weight_per_unit": "300",
        "variants-1-active": "on",
    }

    response = client.post(_edit_url(product), data)

    assert response.status_code == 302
    assert [
        (variant.label, variant.position, variant.weight_per_unit)
        for variant in product.variants.all()
    ] == [
        ("S", 1, 300),
        ("M", 2, product.weight_per_unit),
    ]


@pytest.mark.django_db
def test_two_variants_need_a_label_each(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Hoodie", internal_number=605)

    page = client.get(_edit_url(product))
    data = _page_post_data(page)
    data |= {
        VARIANTS_UNLOCKED_FIELD: "1",
        "variants-TOTAL_FORMS": "2",
        "variants-1-label": "L",
        "variants-1-weight_per_unit": "300",
        "variants-1-active": "on",
    }

    response = client.post(_edit_url(product), data)

    assert response.status_code == 200
    assert response.context["variants_unlocked"] is True
    (first, _second) = response.context["variant_formset"].forms
    assert "each needs a label" in str(first.errors)
    assert product.variants.count() == 1


@pytest.mark.django_db
def test_a_used_variant_cannot_be_deleted_from_the_tab(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Hoodie", internal_number=606)
    variant_factory(product=product, label="M", first_label="S")
    batch_factory(
        product=product,
        variant=product.variants.get(label="S"),
        today=TODAY,
        batch_id="H-1",
    )

    page = client.get(_edit_url(product))
    data = _page_post_data(page)
    data |= {
        VARIANTS_UNLOCKED_FIELD: "1",
        "variants-0-delete": "on",
    }

    response = client.post(_edit_url(product), data)

    assert response.status_code == 200
    assert "pause it instead" in str(
        response.context["variant_formset"].forms[0].errors
    )
    assert product.variants.count() == 2
