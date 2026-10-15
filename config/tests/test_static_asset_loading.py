"""Guard the first ops/public CSS split without requiring browser rendering."""

from pathlib import Path

from django.test import RequestFactory
from django.template.loader import render_to_string


ROOT = Path(__file__).resolve().parents[2]
CSS = ROOT / "static" / "css"


def test_public_bundle_excludes_ops_only_stylesheets():
    public = (CSS / "main.css").read_text()
    for name in ("dashboard.css", "inventory.css", "products.css"):
        assert f'@import url("./{name}")' not in public


def test_ops_bundle_preserves_ops_styles_and_excludes_entrance_styles():
    ops = (CSS / "ops.css").read_text()
    for name in ("dashboard.css", "inventory.css", "products.css"):
        assert f'@import url("./{name}")' in ops
    for name in ("landing.css", "on-blue.css"):
        assert f'@import url("./{name}")' not in ops


def test_base_template_chooses_css_entrypoint_by_route():
    factory = RequestFactory()
    for path, expected, excluded in (
        ("/ops/", "ops.css", "main.css"),
        ("/ops/products/", "ops.css", "main.css"),
        ("/shop/", "main.css", "ops.css"),
        ("/my/", "main.css", "ops.css"),
        ("/accounts/login/", "main.css", "ops.css"),
    ):
        rendered = render_to_string("base.html", request=factory.get(path))
        assert f"css/{expected}" in rendered
        assert f"css/{excluded}" not in rendered
