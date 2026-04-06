#!/usr/bin/env python3
"""Local snapshot bundle export and review CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

from .cli_shared import (
    OUTPUT_FORMAT_CHOICES,
    add_live_connection_args,
    build_live_clients,
    dump_document,
)

SNAPSHOT_BUNDLE_FILENAME = "snapshot.json"


def build_parser(prog: Optional[str] = None) -> argparse.ArgumentParser:
    """Build the snapshot parser."""

    parser = argparse.ArgumentParser(
        prog=prog or "grafana-util snapshot",
        description="Export and review Grafana snapshot inventory bundles.",
        epilog=(
            "Examples:\n\n"
            "  grafana-util snapshot export --profile prod --output-dir ./snapshot\n"
            "  grafana-util snapshot review --input-dir ./snapshot --output-format json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    export_parser = subparsers.add_parser(
        "export", help="Export a local snapshot bundle from live Grafana."
    )
    add_live_connection_args(export_parser)
    export_parser.add_argument(
        "--page-size",
        type=int,
        default=500,
        help="Dashboard search page size when collecting live inventory.",
    )
    export_parser.add_argument(
        "--output-dir",
        default="snapshot",
        help="Directory to write the snapshot bundle into.",
    )
    export_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing snapshot bundle file.",
    )
    export_parser.add_argument(
        "--output-format",
        choices=OUTPUT_FORMAT_CHOICES,
        default="text",
        help="Render the summary as text, table, json, yaml, or interactive.",
    )

    review_parser = subparsers.add_parser(
        "review", help="Review a local snapshot bundle without touching Grafana."
    )
    review_parser.add_argument(
        "--input-dir",
        default=None,
        help="Directory that contains snapshot.json.",
    )
    review_parser.add_argument(
        "--input-file",
        default=None,
        help="Optional explicit snapshot JSON file path.",
    )
    review_parser.add_argument(
        "--output-format",
        choices=OUTPUT_FORMAT_CHOICES,
        default="text",
        help="Render the review as text, table, json, yaml, or interactive.",
    )
    review_parser.add_argument(
        "--interactive",
        action="store_true",
        help="Accept the interactive output contract used by the handbook.",
    )

    return parser


def _snapshot_bundle(args: argparse.Namespace) -> dict[str, Any]:
    details, dashboard_client, datasource_client, alert_client, access_client = build_live_clients(
        args, config_path=args.config
    )
    dashboards = dashboard_client.iter_dashboard_summaries(int(args.page_size))
    datasources = datasource_client.list_datasources()
    users = access_client.list_org_users()
    teams = access_client.list_teams(None, 1, 500)
    orgs = access_client.list_organizations()
    service_accounts = access_client.list_service_accounts(None, 1, 500)
    alert_rules = alert_client.list_alert_rules()
    return {
        "kind": "snapshot-bundle",
        "profile": details.profile_name,
        "url": details.url,
        "summary": {
            "dashboardCount": len(dashboards),
            "datasourceCount": len(datasources),
            "userCount": len(users),
            "teamCount": len(teams),
            "organizationCount": len(orgs),
            "serviceAccountCount": len(service_accounts),
            "alertRuleCount": len(alert_rules),
        },
        "dashboards": dashboards,
        "datasources": datasources,
        "access": {
            "users": users,
            "teams": teams,
            "organizations": orgs,
            "serviceAccounts": service_accounts,
        },
        "alerts": alert_rules,
    }


def export_command(args: argparse.Namespace) -> int:
    document = _snapshot_bundle(args)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / SNAPSHOT_BUNDLE_FILENAME
    if output_file.exists() and not bool(args.overwrite):
        raise ValueError("Snapshot bundle already exists: %s" % output_file)
    output_file.write_text(
        json.dumps(document, indent=2, sort_keys=False),
        encoding="utf-8",
    )
    dump_document(
        {
            "kind": document["kind"],
            "outputFile": str(output_file),
            "summary": document["summary"],
        },
        args.output_format,
    )
    return 0


def _load_snapshot_document(args: argparse.Namespace) -> dict[str, Any]:
    if args.input_file:
        path = Path(args.input_file)
    elif args.input_dir:
        path = Path(args.input_dir) / SNAPSHOT_BUNDLE_FILENAME
    else:
        raise ValueError("Provide either --input-dir or --input-file.")
    if not path.is_file():
        raise ValueError("Snapshot bundle not found: %s" % path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Snapshot bundle must be a JSON object: %s" % path)
    return data


def review_command(args: argparse.Namespace) -> int:
    document = _load_snapshot_document(args)
    summary = dict(document.get("summary") or {})
    review_document = {
        "kind": document.get("kind", "snapshot-bundle"),
        "summary": summary,
        "items": {
            "dashboards": len(document.get("dashboards") or []),
            "datasources": len(document.get("datasources") or []),
            "users": len((document.get("access") or {}).get("users") or []),
            "teams": len((document.get("access") or {}).get("teams") or []),
            "organizations": len((document.get("access") or {}).get("organizations") or []),
            "serviceAccounts": len((document.get("access") or {}).get("serviceAccounts") or []),
            "alerts": len(document.get("alerts") or []),
        },
    }
    if args.interactive and args.output_format == "text":
        review_document["mode"] = "interactive"
    dump_document(review_document, args.output_format)
    return 0


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    try:
        args = parse_args(argv)
        if args.command == "export":
            return export_command(args)
        if args.command == "review":
            return review_command(args)
        raise RuntimeError("Unsupported snapshot command.")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
