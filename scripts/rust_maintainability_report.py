#!/usr/bin/env python3
"""Read-only Rust maintainability reporter.

This helper flags oversized Rust source files and module roots with unusually
large `pub use` surfaces so maintainers can spot refactor pressure without
modifying the tree.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_SOURCE_LINE_LIMIT = 800
DEFAULT_TEST_LINE_LIMIT = 1200
DEFAULT_REEXPORT_LINE_LIMIT = 12


@dataclass(frozen=True)
class RustMaintainabilityFinding:
    path: Path
    category: str
    detail: str


def _count_lines(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return 0


def _count_pub_use_lines(path: Path) -> int:
    try:
        return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.lstrip().startswith("pub use "))
    except OSError:
        return 0


def _line_limit_for(path: Path, source_limit: int, test_limit: int) -> int:
    if "test" in path.name or path.name.endswith("_tests.rs"):
        return test_limit
    return source_limit


def discover_rust_maintainability_findings(
    root: Path,
    *,
    source_line_limit: int = DEFAULT_SOURCE_LINE_LIMIT,
    test_line_limit: int = DEFAULT_TEST_LINE_LIMIT,
    reexport_line_limit: int = DEFAULT_REEXPORT_LINE_LIMIT,
) -> list[RustMaintainabilityFinding]:
    findings: list[RustMaintainabilityFinding] = []
    if not root.exists():
        return findings

    for path in root.rglob("*.rs"):
        if "target" in path.parts:
            continue

        line_count = _count_lines(path)
        if line_count > _line_limit_for(path, source_line_limit, test_line_limit):
            findings.append(
                RustMaintainabilityFinding(
                    path=path,
                    category="oversized-file",
                    detail=f"{line_count} lines",
                )
            )

        reexport_count = _count_pub_use_lines(path)
        if reexport_count >= reexport_line_limit:
            findings.append(
                RustMaintainabilityFinding(
                    path=path,
                    category="reexport-heavy",
                    detail=f"{reexport_count} pub use lines",
                )
            )

    return findings


def render_rust_maintainability_report(
    root: Path,
    *,
    source_line_limit: int = DEFAULT_SOURCE_LINE_LIMIT,
    test_line_limit: int = DEFAULT_TEST_LINE_LIMIT,
    reexport_line_limit: int = DEFAULT_REEXPORT_LINE_LIMIT,
) -> list[str]:
    return [
        f"{item.category}\t{item.detail}\t{item.path}"
        for item in discover_rust_maintainability_findings(
            root,
            source_line_limit=source_line_limit,
            test_line_limit=test_line_limit,
            reexport_line_limit=reexport_line_limit,
        )
    ]


def main() -> int:
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Report oversized Rust files and large re-export surfaces.")
    parser.add_argument("--root", default="rust/src", help="Rust source tree to scan.")
    parser.add_argument("--json", action="store_true", help="Render JSON output.")
    parser.add_argument(
        "--source-line-limit",
        type=int,
        default=DEFAULT_SOURCE_LINE_LIMIT,
        help="Line limit for non-test Rust files.",
    )
    parser.add_argument(
        "--test-line-limit",
        type=int,
        default=DEFAULT_TEST_LINE_LIMIT,
        help="Line limit for Rust test files.",
    )
    parser.add_argument(
        "--reexport-line-limit",
        type=int,
        default=DEFAULT_REEXPORT_LINE_LIMIT,
        help="Minimum pub use count before reporting a module as re-export-heavy.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"Invalid Rust source root: {root}")
        return 2

    findings = discover_rust_maintainability_findings(
        root,
        source_line_limit=args.source_line_limit,
        test_line_limit=args.test_line_limit,
        reexport_line_limit=args.reexport_line_limit,
    )

    if args.json:
        from json import dumps

        print(
            dumps(
                [
                    {"path": str(item.path), "category": item.category, "detail": item.detail}
                    for item in findings
                ],
                indent=2,
                sort_keys=False,
            )
        )
    else:
        for line in render_rust_maintainability_report(
            root,
            source_line_limit=args.source_line_limit,
            test_line_limit=args.test_line_limit,
            reexport_line_limit=args.reexport_line_limit,
        ):
            print(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
