"""Guards the dependency rules documented in ARCHITECTURE.md.

Shared layer rules are derived from the package groups below. Package-specific
ownership rules extend those defaults through FORBIDDEN_IMPORTS.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

PORTALS = frozenset(
    {
        "business_portal",
        "ops_portal",
        "storefront",
    }
)

CHANNEL_APPLICATIONS = frozenset(
    {
        "business",
        "retail",
    }
)

COMPOSITION_ROOT = frozenset(
    {
        "config",
    }
)

SHARED_CAPABILITIES = frozenset(
    {
        "accounts",
        "carts",
        "customers",
        "fulfillment",
        "inventory",
        "orders",
        "payments",
        "pricing",
        "products",
        "reservations",
    }
)

_SHARED_CAPABILITY_FORBIDDEN_IMPORTS = (
    PORTALS
    | CHANNEL_APPLICATIONS
    | COMPOSITION_ROOT
)

FORBIDDEN_IMPORTS: dict[str, frozenset[str]] = {
    package: _SHARED_CAPABILITY_FORBIDDEN_IMPORTS
    for package in SHARED_CAPABILITIES
}

FORBIDDEN_IMPORTS.update(
    {
        "business": PORTALS | COMPOSITION_ROOT,
        "retail": PORTALS | COMPOSITION_ROOT,
        "inventory": (
            FORBIDDEN_IMPORTS["inventory"]
            | {"reservations"}
        ),
        "orders": (
            FORBIDDEN_IMPORTS["orders"]
            | {"reservations"}
        ),
        "products": (
            FORBIDDEN_IMPORTS["products"]
            | {"orders"}
        ),
    }
)


def _scanned_files(package: str) -> list[Path]:
    return sorted(
        path
        for path in (ROOT / package).rglob("*.py")
        if "tests" not in path.parts and "migrations" not in path.parts
    )


def _imported_top_level_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.add(node.module.split(".")[0])

    return modules


@pytest.mark.parametrize("package", sorted(FORBIDDEN_IMPORTS))
def test_package_does_not_import_forbidden_packages(package: str) -> None:
    forbidden = FORBIDDEN_IMPORTS[package]
    violations = [
        f"{path.relative_to(ROOT)} imports {sorted(found)}"
        for path in _scanned_files(package)
        if (found := _imported_top_level_modules(path) & forbidden)
    ]

    assert not violations, "\n".join(violations)
