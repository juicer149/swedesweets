"""List CSS classes that nothing uses any more.

Reads every class selector in static/css and looks for it in templates,
static/js, static/vendor and the Python apps (view models build class
names too).
Prints the unused ones per CSS file with their line. With --delete it
also removes them: a selector that names an unused class is dropped from
its rule, and a rule with no selectors left goes entirely (empty @media
blocks too). Comments stay; read the diff, tidy them, run the tests.

Class names built at runtime count as used through their fixed start:
`order-status--{{ order.status }}` in a template, or
f"button--tone-{tone}" in Python, marks every class starting with
`order-status--` or `button--tone-` as used.

    python tools/css_unused.py                     # all CSS files
    python tools/css_unused.py page.css            # only these files
    python tools/css_unused.py --delete            # and remove them
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS_DIR = ROOT / "static" / "css"
SKIP_DIRS = {".venv", "node_modules", "staticfiles", ".git", "media"}

CLASS_IN_SELECTOR = re.compile(r"\.(-?[a-zA-Z_][\w-]*)")
TOKEN = re.compile(r"[a-zA-Z_][\w-]*")
# A class name cut off where a template variable, tag, |add: or an
# f-string field starts: "order-status--{{", "tone-"|add:, f"tone-{x}".
DYNAMIC_PREFIX = re.compile(r"([a-zA-Z_][\w-]*[-_])(?=\{\{|\{%|\"\|add:|'\|add:|\{)")


def _source_files() -> list[Path]:
    files: list[Path] = []

    # static/vendor: libraries such as Tom Select add their own classes
    # (.ts-wrapper, .ts-dropdown) that the site's CSS styles.
    patterns = (
        "templates/**/*.html",
        "static/js/**/*.js",
        "static/vendor/**/*.js",
        "**/*.py",
    )

    for pattern in patterns:
        for path in ROOT.glob(pattern):
            if SKIP_DIRS.intersection(path.relative_to(ROOT).parts):
                continue
            if path.name == Path(__file__).name:
                continue
            files.append(path)

    return files


def _strip_comments(css: str) -> str:
    return re.sub(
        r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), css, flags=re.S
    )


def _css_classes(path: Path) -> dict[str, int]:
    """Class name -> first line it appears on in a selector."""

    css = _strip_comments(path.read_text())
    classes: dict[str, int] = {}
    # Only text before a "{" is a selector; declarations are skipped.
    for block in re.finditer(r"([^{}]*)\{", css):
        selector = block.group(1)
        line = css.count("\n", 0, block.start(1)) + 1
        if selector.strip().startswith("@"):
            continue
        for match in CLASS_IN_SELECTOR.finditer(selector):
            name = match.group(1)
            # Skip numbers in values that leaked in, e.g. ".5rem".
            if name[0].isdigit():
                continue
            offset = selector.count("\n", 0, match.start())
            classes.setdefault(name, line + offset)

    return classes


LEAF_RULE = re.compile(r"(?P<head>[^{}]*?)\{(?P<body>[^{}]*)\}")


def _split_selectors(selector: str) -> list[str]:
    """Split on top-level commas, not those inside :not(a, b)."""

    items, depth, current = [], 0, ""

    for char in selector:
        if char in "([":
            depth += 1
        elif char in ")]":
            depth -= 1
        if char == "," and depth == 0:
            items.append(current)
            current = ""
        else:
            current += char

    items.append(current)
    return items


def _delete_unused(css: str, unused: set[str]) -> str:
    def rewrite(match: re.Match) -> str:
        head, body = match.group("head"), match.group("body")
        # Comments and blank lines before the selector are kept as they are.
        cut = head.rfind("*/") + 2 if "*/" in head else 0
        prefix, selector = head[:cut], head[cut:]

        if selector.strip().startswith("@"):
            return match.group(0)

        items = _split_selectors(selector)
        alive = [
            item
            for item in items
            if not unused.intersection(CLASS_IN_SELECTOR.findall(item))
        ]

        if len(alive) == len(items):
            return match.group(0)
        if not alive:
            return prefix

        kept = ",".join(alive)
        leading = selector[: len(selector) - len(selector.lstrip())]
        return prefix + leading + kept.strip() + " {" + body + "}"

    css = LEAF_RULE.sub(rewrite, css)

    # @media blocks left with nothing inside.
    empty_block = re.compile(r"@media[^{}]*\{\s*\}")
    while empty_block.search(css):
        css = empty_block.sub("", css)

    return re.sub(r"\n{4,}", "\n\n\n", css)


def main(argv: list[str]) -> int:
    delete = "--delete" in argv
    argv = [arg for arg in argv if arg != "--delete"]

    css_files = (
        [CSS_DIR / name for name in argv] if argv else sorted(CSS_DIR.glob("*.css"))
    )

    used_tokens: set[str] = set()
    used_prefixes: set[str] = set()

    for path in _source_files():
        text = path.read_text(errors="ignore")
        used_tokens.update(TOKEN.findall(text))
        used_prefixes.update(DYNAMIC_PREFIX.findall(text))

    total = 0

    for css_path in css_files:
        unused = [
            (line, name)
            for name, line in _css_classes(css_path).items()
            if name not in used_tokens
            and not any(name.startswith(prefix) for prefix in used_prefixes)
        ]

        if not unused:
            continue

        total += len(unused)
        print(f"\n{css_path.relative_to(ROOT)} ({len(unused)})")
        for line, name in sorted(unused):
            print(f"  {line:>5}  .{name}")

        if delete:
            css_path.write_text(
                _delete_unused(
                    css_path.read_text(),
                    {name for _, name in unused},
                )
            )

    verb = "removed" if delete else "unused"
    print(f"\n{total} {verb} class{'es' if total != 1 else ''}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
