"""Protect the two CSS surfaces and their transitive asset dependencies."""
import re
from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.test import RequestFactory

from config.context_processors import static_assets

CSS_ROOT = settings.BASE_DIR / "static" / "css"
IMPORT = re.compile(r'@import\s+url\(["\']([^"\']+)["\']\)')
URL = re.compile(r'url\(["\']?([^"\')]+)["\']?\)')


def _imports(path: Path, visited: set[Path] | None = None) -> set[Path]:
    visited = set() if visited is None else visited
    path = path.resolve()
    if path in visited:
        return visited
    visited.add(path)
    for relative in IMPORT.findall(path.read_text()):
        _imports(path.parent / relative, visited)
    return visited


@pytest.mark.parametrize("path,expected", [
    ("/", "css/public.css"),
    ("/shop/", "css/public.css"),
    ("/my/catalog/", "css/public.css"),
    ("/accounts/login/", "css/public.css"),
    ("/ops/", "css/ops.css"),
    ("/ops/orders/123/pack/", "css/ops.css"),
])
def test_stylesheet_follows_surface_not_account_role(path, expected):
    request = RequestFactory().get(path)
    # Identity must not turn a staff member's shop visit into an ops page.
    request.account_role = object()
    assert static_assets(request)["site_stylesheet"] == expected


def test_error_template_without_request_has_public_styles():
    html = render_to_string("base.html")
    assert "css/public" in html


def test_zone_bundles_share_components_but_not_page_styles():
    public = _imports(CSS_ROOT / "public.css")
    ops = _imports(CSS_ROOT / "ops.css")
    assert not any(p.parent.name == "ops" for p in public)
    assert not any(p.parent.name == "public" for p in ops)
    # Previous orders uses the same expandable rows in B2B and ops.
    assert (CSS_ROOT / "common/accordion.css").resolve() in public & ops
    # Every stylesheet has an owner and is reachable from a real entrypoint.
    assert {p.resolve() for p in CSS_ROOT.rglob("*.css")} == public | ops


def test_relative_assets_resolve_after_stylesheets_move():
    for path in CSS_ROOT.rglob("*.css"):
        for reference in URL.findall(path.read_text()):
            if reference.startswith(("#", "data:", "http:", "https:")):
                continue
            target = (path.parent / reference).resolve()
            assert target.is_file(), f"{path.relative_to(CSS_ROOT)}: {reference}"
            static_path = target.relative_to(settings.BASE_DIR / "static")
            assert finders.find(str(static_path))
