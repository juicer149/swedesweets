from types import SimpleNamespace

import pytest
from django.core.cache import cache

from products.images import _image_url


class SignedImage:
    def __init__(self, name="products/test-url.webp", bucket="test"):
        self.name = name
        self.storage = SimpleNamespace(bucket_name=bucket, endpoint_url="https://media")
        self.signatures = 0

    @property
    def url(self):
        self.signatures += 1
        return f"https://media/{self.name}?signature={self.signatures}"


@pytest.fixture(autouse=True)
def isolated_image_cache():
    cache.clear()
    yield
    cache.clear()


def test_signed_images_reuse_urls_but_renew_after_cache_expiry(settings):
    settings.USE_S3_MEDIA = True
    image = SignedImage()
    first = _image_url(image)
    assert _image_url(image) == first
    assert image.signatures == 1
    cache.clear()  # Same outcome as the short cache lifetime expiring.
    assert _image_url(image) != first


def test_replaced_images_and_separate_buckets_do_not_reuse_old_urls(settings):
    settings.USE_S3_MEDIA = True
    original = SignedImage()
    _image_url(original)
    replaced = SignedImage(name="products/replacement.webp")
    assert "replacement.webp" in _image_url(replaced)
    other_bucket = SignedImage(bucket="other")
    _image_url(other_bucket)
    assert other_bucket.signatures == 1


def test_local_media_does_not_cache_storage_urls(settings):
    settings.USE_S3_MEDIA = False
    image = SignedImage()
    assert _image_url(image) != _image_url(image)
