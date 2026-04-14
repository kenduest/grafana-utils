#!/usr/bin/env python3
"""Read-only Rust maintainability reporter.

This helper flags oversized Rust source files, module roots with unusually
large `pub use` surfaces, and directory summaries so maintainers can spot
refactor pressure without modifying the tree.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_SOURCE_LINE_LIMIT = 800
DEFAULT_TEST_LINE_LIMIT = 1200
DEFAULT_REEXPORT_LINE_LIMIT = 12
DEFAULT_SUMMARY_HOTSPOT_LIMIT = 5


@dataclass(frozen=True)
class RustMaintainabilityFinding:
    path: Path
    category: str
    detail: str


@dataclass(frozen=True)
class RustMaintainabilityHotspot:
    path: Path
    line_count: int


@dataclass(frozen=True)
class RustMaintainabilityDirectorySummary:
    path: Path
    file_count: int
    line_count: int
    hotspots: tuple[RustMaintainabilityHotspot, ...]


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


def _rust_files_under(root: Path) -> list[Path]:
    if not root.exists():
        return []
    if root.is_file():
        root = root.parent
    return [path for path in root.rglob("*.rs") if "target" not in path.parts]


def _line_limit_for(path: Path, source_limit: int, test_limit: int) -> int:
    if "test" in path.name or path.name.endswith("_tests.rs"):
        return test_limit
    return source_limit


def discover_rust_maintainability_directory_summaries(
    roots: Iterable[Path],
    *,
    hotspot_limit: int = DEFAULT_SUMMARY_HOTSPOT_LIMIT,
) -> list[RustMaintainabilityDirectorySummary]:
    summaries: list[RustMaintainabilityDirectorySummary] = []
    seen: set[Path] = set()
    for root in roots:
        directory = root.resolve()
        if directory in seen:
            continue
        seen.add(directory)
        files = _rust_files_under(directory)
        if not files:
            continue

        file_line_counts = [(path, _count_lines(path)) for path in files]
        file_line_counts.sort(key=lambda item: (-item[1], item[0].as_posix()))
        summaries.append(
            RustMaintainabilityDirectorySummary(
                path=directory,
                file_count=len(file_line_counts),
                line_count=sum(line_count for _, line_count in file_line_counts),
                hotspots=tuple(
                    RustMaintainabilityHotspot(path=path, line_count=line_count)
                    for path, line_count in file_line_counts[:hotspot_limit]
                ),
            )
        )
    return summaries


def _format_directory_summary(summary: RustMaintainabilityDirectorySummary) -> str:
    hotspots = ", ".join(
        f"{hotspot.path} ({hotspot.line_count} lines)"
        for hotspot in summary.hotspots
    )
    hotspot_detail = f"; hotspots: {hotspots}" if hotspots else ""
    return f"{summary.file_count} files, {summary.line_count} lines{hotspot_detail}"


def _render_directory_summary_line(summary: RustMaintainabilityDirectorySummary) -> str:
    return f"directory-summary\t{_format_directory_summary(summary)}\t{summary.path}"


def _render_directory_summary_json(summary: RustMaintainabilityDirectorySummary) -> dict[str, object]:
    return {
        "path": str(summary.path),
        "category": "directory-summary",
        "detail": _format_directory_summary(summary),
        "file_count": summary.file_count,
        "line_count": summary.line_count,
        "hotspots": [
            {"path": str(hotspot.path), "line_count": hotspot.line_count}
            for hotspot in summary.hotspots
        ],
    }


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
    summary_roots: Iterable[Path] | None = None,
    summary_hotspot_limit: int = DEFAULT_SUMMARY_HOTSPOT_LIMIT,
    source_line_limit: int = DEFAULT_SOURCE_LINE_LIMIT,
    test_line_limit: int = DEFAULT_TEST_LINE_LIMIT,
    reexport_line_limit: int = DEFAULT_REEXPORT_LINE_LIMIT,
) -> list[str]:
    lines: list[str] = []
    for summary in discover_rust_maintainability_directory_summaries(
        summary_roots or [],
        hotspot_limit=summary_hotspot_limit,
    ):
        lines.append(_render_directory_summary_line(summary))

    lines.extend(
        f"{item.category}\t{item.detail}\t{item.path}"
        for item in discover_rust_maintainability_findings(
            root,
            source_line_limit=source_line_limit,
            test_line_limit=test_line_limit,
            reexport_line_limit=reexport_line_limit,
        )
    )
    return lines


def main() -> int:
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Report oversized Rust files and large re-export surfaces.")
    parser.add_argument("--root", default="rust/src", help="Rust source tree to scan.")
    parser.add_argument("--json", action="store_true", help="Render JSON output.")
    parser.add_argument(
        "--summary-root",
        action="append",
        default=[],
        help="Directory to summarize; may be repeated.",
    )
    parser.add_argument(
        "--summary-hotspots",
        type=int,
        default=DEFAULT_SUMMARY_HOTSPOT_LIMIT,
        help="Number of hotspot files to include in each directory summary.",
    )
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
    summaries = discover_rust_maintainability_directory_summaries(
        [Path(path) for path in args.summary_root],
        hotspot_limit=args.summary_hotspots,
    )

    if args.json:
        from json import dumps

        print(
            dumps(
                [
                    *(_render_directory_summary_json(item) for item in summaries),
                    *(
                        {"path": str(item.path), "category": item.category, "detail": item.detail}
                        for item in findings
                    ),
                ],
                indent=2,
                sort_keys=False,
            )
        )
    else:
        for line in render_rust_maintainability_report(
            root,
            summary_roots=[Path(path) for path in args.summary_root],
            summary_hotspot_limit=args.summary_hotspots,
            source_line_limit=args.source_line_limit,
            test_line_limit=args.test_line_limit,
            reexport_line_limit=args.reexport_line_limit,
        ):
            print(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
