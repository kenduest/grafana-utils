#!/usr/bin/env python3
"""Check high-signal Rust architecture guardrails for the repo."""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUST_DIR = REPO_ROOT / "rust"
RUST_SRC_DIR = RUST_DIR / "src"

RUST_ROOT_ALLOWLIST = {
    "rust/.gitignore",
    "rust/Cargo.lock",
    "rust/Cargo.toml",
    "rust/build.rs",
}

MOD_RS_HARD_LIMIT = 800
CLI_RS_HARD_LIMIT = 700
CLI_DISPATCH_RS_HARD_LIMIT = 300
PRODUCTION_WARN_LIMIT = 900
TEST_WARN_LIMIT = 1200

RAW_API_PATH_RE = re.compile(r'"/api/[^"\n]+')
TRAVERSAL_RE = re.compile(r"(\.\./|\.\.\\|Path::new\(\s*\"\.{2}\"|join\(\s*\"\.{2}\"\))")


@dataclass(frozen=True)
class Finding:
    severity: str
    path: str
    message: str


def relpath(path: str | Path) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            candidate = candidate.relative_to(REPO_ROOT)
        except ValueError:
            pass
    return candidate.as_posix().lstrip("./")


def git_output(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def parse_git_status_paths() -> dict[str, str]:
    status: dict[str, str] = {}
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", "rust"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return status

    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        status[relpath(path)] = line[:2]
    return status


def rust_root_entries() -> set[str]:
    tracked = {
        relpath(path)
        for path in git_output("ls-files", "rust")
        if Path(path).parent == Path("rust")
    }
    visible = {
        relpath(path)
        for path in RUST_DIR.iterdir()
        if path.is_file()
    }
    status = set(parse_git_status_paths())
    return tracked | visible | status


def root_noise_finding(path: str, status: dict[str, str]) -> Finding | None:
    if not path.startswith("rust/"):
        return None
    if path in RUST_ROOT_ALLOWLIST:
        return None
    if Path(path).parent.as_posix() != "rust":
        return None

    status_code = status.get(path)
    details: list[str] = []
    if status_code is not None:
        if status_code == "??":
            details.append("untracked in git status")
        elif status_code.strip() == "D":
            return Finding(
                severity="warning",
                path=path,
                message="deleted cleanup artifact in git status",
            )
        else:
            details.append(f"visible in git status ({status_code.strip() or 'tracked'})")
    else:
        details.append("tracked root file")

    return Finding(
        severity="hard-fail",
        path=path,
        message="root rust/ noise file: " + ", ".join(details),
    )


def classify_rust_file(path: Path) -> str:
    name = path.name
    if name == "mod.rs":
        return "mod"
    if name == "cli.rs":
        return "cli"
    if name == "cli_dispatch.rs":
        return "dispatch"
    if name.endswith("_rust_tests.rs") or "tests" in name:
        return "test"
    return "production"


def file_lines(path: Path) -> int:
    return path.read_text(encoding="utf-8").count("\n") + 1


def detect_size_issues() -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(RUST_SRC_DIR.rglob("*.rs")):
        if "target" in path.parts:
            continue
        lines = file_lines(path)
        rel = relpath(path)
        kind = classify_rust_file(path)

        if kind == "mod" and lines > MOD_RS_HARD_LIMIT:
            findings.append(
                Finding(
                    severity="hard-fail",
                    path=rel,
                    message=f"mod.rs is {lines} lines, over the {MOD_RS_HARD_LIMIT}-line limit",
                )
            )
        elif kind == "cli" and lines > CLI_RS_HARD_LIMIT:
            findings.append(
                Finding(
                    severity="hard-fail",
                    path=rel,
                    message=f"cli.rs is {lines} lines, over the {CLI_RS_HARD_LIMIT}-line limit",
                )
            )
        elif kind == "dispatch" and lines > CLI_DISPATCH_RS_HARD_LIMIT:
            findings.append(
                Finding(
                    severity="hard-fail",
                    path=rel,
                    message=(
                        f"cli_dispatch.rs is {lines} lines, over the {CLI_DISPATCH_RS_HARD_LIMIT}-line limit"
                    ),
                )
            )
        elif kind == "test" and lines >= TEST_WARN_LIMIT:
            findings.append(
                Finding(
                    severity="warning",
                    path=rel,
                    message=f"test file is {lines} lines, over the {TEST_WARN_LIMIT}-line warning threshold",
                )
            )
        elif kind == "production" and lines >= PRODUCTION_WARN_LIMIT:
            findings.append(
                Finding(
                    severity="warning",
                    path=rel,
                    message=(
                        f"production file is {lines} lines, over the {PRODUCTION_WARN_LIMIT}-line warning threshold"
                    ),
                )
            )

    return findings


def detect_render_risks() -> list[Finding]:
    findings: list[Finding] = []
    render_files = [
        path
        for path in RUST_SRC_DIR.rglob("*.rs")
        if "target" not in path.parts
        and "render" in path.name
        and not path.name.endswith("_rust_tests.rs")
    ]
    for path in render_files:
        text = path.read_text(encoding="utf-8")
        hits: list[str] = []
        if RAW_API_PATH_RE.search(text):
            hits.append("raw API path literals")
        if TRAVERSAL_RE.search(text):
            hits.append("filesystem traversal patterns")
        if hits:
            findings.append(
                Finding(
                    severity="warning",
                    path=relpath(path),
                    message="render file contains " + " and ".join(hits),
                )
            )
    return findings


def detect_help_test_risks() -> list[Finding]:
    findings: list[Finding] = []
    for path in RUST_SRC_DIR.rglob("*help*_rust_tests.rs"):
        if "target" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        contains_count = text.count("help.contains(")
        render_help_count = text.count("render_help()") + text.count("write_long_help(")
        brittle_eq_patterns = (
            "assert_eq!(help",
            "assert_eq!(rendered",
            "assert_eq!(output",
            "assert_eq!(text",
            "assert_eq!(rendered_help",
        )

        if render_help_count and any(pattern in text for pattern in brittle_eq_patterns):
            findings.append(
                Finding(
                    severity="warning",
                    path=relpath(path),
                    message="help test compares rendered help output directly; consider semantic assertions instead",
                )
            )
        elif contains_count >= 12 and render_help_count:
            findings.append(
                Finding(
                    severity="warning",
                    path=relpath(path),
                    message=(
                        f"help test uses {contains_count} help.contains() assertions; consider narrower semantic checks"
                    ),
                )
            )
    return findings


def gather_findings() -> list[Finding]:
    findings: list[Finding] = []

    root_status = parse_git_status_paths()
    for path in sorted(rust_root_entries()):
        finding = root_noise_finding(path, root_status)
        if finding is not None:
            findings.append(finding)

    findings.extend(detect_size_issues())
    findings.extend(detect_render_risks())
    findings.extend(detect_help_test_risks())
    return findings


def print_report(findings: list[Finding]) -> None:
    hard = [finding for finding in findings if finding.severity == "hard-fail"]
    warnings = [finding for finding in findings if finding.severity == "warning"]

    print("rust-architecture report")
    print(f"  hard failures: {len(hard)}")
    print(f"  warnings: {len(warnings)}")

    if hard:
        print("hard failures:")
        for finding in hard:
            print(f"  - {finding.path}: {finding.message}")

    if warnings:
        print("warnings:")
        for finding in warnings:
            print(f"  - {finding.path}: {finding.message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check Rust architecture guardrails for the repo."
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Print the report but always exit 0.",
    )
    args = parser.parse_args(argv)

    findings = gather_findings()
    if not findings:
        print("check_rust_architecture: ok")
        return 0

    print_report(findings)
    if args.warn_only:
        return 0
    return 1 if any(finding.severity == "hard-fail" for finding in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
