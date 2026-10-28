import pytest
from django.utils.translation import override

from products.models import Product, ProductProfile, ProductVariant
from products.presentation import cart_variant_label
from products.tests.factories import product_factory, variant_factory


def loaded(product):
    return Product.objects.select_related("profile").prefetch_related("variants").get(
        pk=product.pk
    )


@pytest.mark.django_db
def test_sole_legacy_name_is_not_a_customer_variant(django_assert_num_queries):
    product = product_factory(name="Djungelvrål", weight_per_unit=2000)
    variant = product.variants.get()
    ProductVariant.objects.filter(pk=variant.pk).update(label="Djungelvrål 2000")
    product = loaded(product)
    with override("fr"), django_assert_num_queries(0):
        assert cart_variant_label(product, product.variants.all()[0]) == "2000 g"


@pytest.mark.django_db
def test_merchandise_shows_selected_size_without_shipping_weight():
    product = product_factory(name="Hoodie", weight_per_unit=400)
    ProductProfile.objects.filter(product=product).update(
        category=ProductProfile.Category.MERCHANDISE
    )
    variant = variant_factory(product=product, label="M", first_label="S")
    assert cart_variant_label(loaded(product), variant) == "M"


@pytest.mark.django_db
def test_sole_merchandise_size_is_still_useful():
    product = product_factory(name="Hoodie", weight_per_unit=400)
    ProductProfile.objects.filter(product=product).update(
        category=ProductProfile.Category.MERCHANDISE
    )
    variant = product.variants.get()
    ProductVariant.objects.filter(pk=variant.pk).update(label="M")
    product = loaded(product)
    assert cart_variant_label(product, product.variants.all()[0]) == "M"


@pytest.mark.django_db
def test_weight_choice_does_not_repeat_the_weight():
    product = product_factory(weight_per_unit=60)
    variant = variant_factory(
        product=product, label="150 g", first_label="60 g", weight_per_unit=150
    )
    assert cart_variant_label(loaded(product), variant) == "150 g"
