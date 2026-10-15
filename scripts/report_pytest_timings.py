"""Summarize pytest --durations=0 output by app and test phase.

This is diagnostic only: timings overlap with framework overhead and should not
be interpreted as a complete wall-clock breakdown.
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

DURATION = re.compile(r"^\s*(\d+(?:\.\d+)?)s\s+(setup|call|teardown)\s+(.+?)\s*$")


def main(path: Path) -> None:
    totals: dict[str, dict[str, float]] = defaultdict(
        lambda: {"setup": 0.0, "call": 0.0, "teardown": 0.0}
    )
    counts: dict[str, int] = defaultdict(int)
    entries: list[tuple[float, str, str]] = []

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = DURATION.match(line)
        if not match:
            continue
        seconds, phase, nodeid = match.groups()
        app = nodeid.split("/", 1)[0]
        duration = float(seconds)
        totals[app][phase] += duration
        if phase == "call":
            counts[app] += 1
        entries.append((duration, phase, nodeid))

    if not entries:
        raise SystemExit("No pytest durations found; check --durations=0 output")

    print("\n=== Pytest measured durations by app (seconds) ===")
    print(f"{'App':28} {'Setup':>9} {'Call':>9} {'Teardown':>9} {'Total':>9} {'Calls':>7}")
    for app, phases in sorted(
        totals.items(), key=lambda item: -sum(item[1].values())
    ):
        total = sum(phases.values())
        print(
            f"{app:28} {phases['setup']:9.2f} {phases['call']:9.2f} "
            f"{phases['teardown']:9.2f} {total:9.2f} {counts[app]:7}"
        )

    print("\n=== Slowest 20 measured phases ===")
    for seconds, phase, nodeid in sorted(entries, reverse=True)[:20]:
        print(f"{seconds:6.2f}s {phase:8} {nodeid}")

    print(
        "\nNote: pytest reports durations rounded to 0.01s; totals are "
        "approximate and exclude unmeasured collection/runner overhead."
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/report_pytest_timings.py pytest-timings.log")
    main(Path(sys.argv[1]))
