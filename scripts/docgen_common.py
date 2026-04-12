"""Shared helpers for generated documentation artifacts.

Keep this file small and boring. The goal is to give maintainers one obvious
place for repo-path resolution and generated-output write/check/report logic.
"""

from __future__ import annotations

from pathlib import Path
from posixpath import relpath


REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()


def relative_href(from_rel: str, to_rel: str) -> str:
    """Return a browser-friendly relative link between two generated outputs."""
    return relpath(to_rel, start=str(Path(from_rel).parent)).replace("\\", "/")


def existing_output_files(output_root: Path) -> set[str]:
    if not output_root.exists():
        return set()
    return {
        path.relative_to(output_root).as_posix()
        for path in output_root.rglob("*")
        if path.is_file()
    }


def write_outputs(output_root: Path, outputs: dict[str, str], *, prune: bool = False) -> None:
    """Write repo-relative generated files under one output root."""
    output_root.mkdir(parents=True, exist_ok=True)
    if prune:
        stale_outputs = existing_output_files(output_root) - set(outputs)
        for relative_path in sorted(stale_outputs):
            (output_root / relative_path).unlink()
    for relative_path, content in outputs.items():
        output_path = output_root / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")


def check_outputs(
    output_root: Path,
    outputs: dict[str, str],
    label: str,
    regenerate_command: str,
    *,
    prune: bool = False,
) -> int:
    """Return non-zero when checked-in generated outputs are stale."""
    stale: list[str] = []
    for relative_path, content in outputs.items():
        output_path = output_root / relative_path
        if not output_path.exists() or output_path.read_text(encoding="utf-8") != content:
            stale.append(relative_path)
    if prune:
        stale.extend(sorted(existing_output_files(output_root) - set(outputs)))
    if stale:
        print(f"Generated {label} are out of date:")
        for relative_path in stale:
            print(f"  {relative_path}")
        print(f"Run: {regenerate_command}")
        return 1
    print(f"Generated {label} are up to date.")
    return 0


def print_written_outputs(
    output_root: Path,
    outputs: dict[str, str],
    label: str,
    source_glob: str,
    output_glob: str,
    entrypoint: str,
) -> None:
    """Print a short, maintainer-friendly regeneration summary."""
    print(f"Wrote {len(outputs)} {label}.")
    print(f"  from {source_glob}")
    print(f"  to   {output_glob}")
    print(f"  open {entrypoint}")
