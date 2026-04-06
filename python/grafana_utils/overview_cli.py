#!/usr/bin/env python3
"""Project-wide overview summaries for the Python CLI."""

from __future__ import annotations

import argparse
import sys
from typing import Any, Optional

from .cli_shared import (
    OUTPUT_FORMAT_CHOICES,
    add_live_connection_args,
    build_live_clients,
    dump_document,
    summarize_path,
)


def build_parser(prog: Optional[str] = None) -> argparse.ArgumentParser:
    """Build the overview parser."""

    parser = argparse.ArgumentParser(
        prog=prog or "grafana-util overview",
        description="Render project-wide staged or live overview summaries.",
        epilog=(
            "Examples:\n\n"
            "  grafana-util overview live --profile prod --output-format yaml\n"
            "  grafana-util overview staged --dashboard-export-dir ./dashboards/raw --desired-file ./desired.json --output-format json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    live_parser = subparsers.add_parser(
        "live", help="Summarize live Grafana state from a reusable connection."
    )
    add_live_connection_args(live_parser)
    live_parser.add_argument(
        "--page-size",
        type=int,
        default=500,
        help="Dashboard search page size when collecting live state.",
    )
    live_parser.add_argument(
        "--output-format",
        choices=OUTPUT_FORMAT_CHOICES,
        default="text",
        help="Render the result as text, table, json, yaml, or interactive.",
    )

    staged_parser = subparsers.add_parser(
        "staged", help="Summarize staged artifacts from the local checkout."
    )
    for flag in (
        "--dashboard-export-dir",
        "--dashboard-provisioning-dir",
        "--datasource-export-dir",
        "--datasource-provisioning-file",
        "--access-user-export-dir",
        "--access-team-export-dir",
        "--access-org-export-dir",
        "--access-service-account-export-dir",
        "--desired-file",
        "--source-bundle",
        "--target-inventory",
        "--alert-export-dir",
        "--availability-file",
        "--mapping-file",
    ):
        staged_parser.add_argument(flag, default=None)
    staged_parser.add_argument(
        "--output-format",
        choices=OUTPUT_FORMAT_CHOICES,
        default="text",
        help="Render the result as text, table, json, yaml, or interactive.",
    )

    return parser


def _live_summary(args: argparse.Namespace) -> dict[str, Any]:
    details, dashboard_client, datasource_client, alert_client, access_client = build_live_clients(
        args, config_path=args.config
    )
    return {
        "kind": "overview-live",
        "profile": details.profile_name,
        "url": details.url,
        "summary": {
            "dashboardCount": len(dashboard_client.iter_dashboard_summaries(int(args.page_size))),
            "datasourceCount": len(datasource_client.list_datasources()),
            "alertRuleCount": len(alert_client.list_alert_rules()),
            "organizationCount": len(access_client.list_organizations()),
            "orgUserCount": len(access_client.list_org_users()),
        },
    }


def _staged_summary(args: argparse.Namespace) -> dict[str, Any]:
    input_paths = {
        "dashboardExportDir": args.dashboard_export_dir,
        "dashboardProvisioningDir": args.dashboard_provisioning_dir,
        "datasourceExportDir": args.datasource_export_dir,
        "datasourceProvisioningFile": args.datasource_provisioning_file,
        "accessUserExportDir": args.access_user_export_dir,
        "accessTeamExportDir": args.access_team_export_dir,
        "accessOrgExportDir": args.access_org_export_dir,
        "accessServiceAccountExportDir": args.access_service_account_export_dir,
        "desiredFile": args.desired_file,
        "sourceBundle": args.source_bundle,
        "targetInventory": args.target_inventory,
        "alertExportDir": args.alert_export_dir,
        "availabilityFile": args.availability_file,
        "mappingFile": args.mapping_file,
    }
    summaries = {
        key: value
        for key, value in ((
            name,
            summarize_path(path),
        ) for name, path in input_paths.items())
        if value is not None
    }
    return {
        "kind": "overview-staged",
        "summary": {
            "inputCount": len(summaries),
            "existingCount": len([item for item in summaries.values() if item.get("exists")]),
            "fileCount": len([item for item in summaries.values() if item.get("kind") == "file"]),
            "dirCount": len([item for item in summaries.values() if item.get("kind") == "dir"]),
        },
        "inputs": summaries,
    }


def live_command(args: argparse.Namespace) -> int:
    dump_document(_live_summary(args), args.output_format)
    return 0


def staged_command(args: argparse.Namespace) -> int:
    dump_document(_staged_summary(args), args.output_format)
    return 0


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    try:
        args = parse_args(argv)
        if args.command == "live":
            return live_command(args)
        if args.command == "staged":
            return staged_command(args)
        raise RuntimeError("Unsupported overview command.")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
