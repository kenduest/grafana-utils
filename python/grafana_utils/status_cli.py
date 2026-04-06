#!/usr/bin/env python3
"""Shared readiness/status summaries for the Python CLI."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from . import overview_cli
from .cli_shared import dump_document


def build_parser(prog: Optional[str] = None) -> argparse.ArgumentParser:
    """Build the status parser."""

    return overview_cli.build_parser(prog=prog or "grafana-util status")


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def live_command(args: argparse.Namespace) -> int:
    document = overview_cli._live_summary(args)
    document["kind"] = "status-live"
    document["status"] = "ok"
    dump_document(document, args.output_format)
    return 0


def staged_command(args: argparse.Namespace) -> int:
    document = overview_cli._staged_summary(args)
    document["kind"] = "status-staged"
    document["status"] = "ok"
    dump_document(document, args.output_format)
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    try:
        args = parse_args(argv)
        if args.command == "live":
            return live_command(args)
        if args.command == "staged":
            return staged_command(args)
        raise RuntimeError("Unsupported status command.")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
