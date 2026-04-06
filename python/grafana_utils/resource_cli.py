#!/usr/bin/env python3
"""Read-only generic Grafana resource surface for the Python CLI."""

from __future__ import annotations

import argparse
import sys
from typing import Any, Optional

from .cli_shared import (
    OUTPUT_FORMAT_CHOICES,
    add_live_connection_args,
    build_live_clients,
    dump_document,
)

SUPPORTED_RESOURCE_KIND_INFO = {
    "dashboards": {
        "description": "Live dashboard inventory and full dashboard payloads.",
        "list": "GET /api/search?type=dash-db",
        "get": "GET /api/dashboards/uid/<uid>",
    },
    "folders": {
        "description": "Live folder inventory and full folder payloads.",
        "list": "GET /api/folders",
        "get": "GET /api/folders/<uid>",
    },
    "datasources": {
        "description": "Live datasource inventory and full datasource payloads.",
        "list": "GET /api/datasources",
        "get": "GET /api/datasources/uid/<uid>",
    },
    "alert-rules": {
        "description": "Live alert-rule inventory and full alert-rule payloads.",
        "list": "GET /api/v1/provisioning/alert-rules",
        "get": "GET /api/v1/provisioning/alert-rules/<uid>",
    },
    "orgs": {
        "description": "Live organization inventory and full organization payloads.",
        "list": "GET /api/orgs",
        "get": "GET /api/orgs/<id>",
    },
}


def build_parser(prog: Optional[str] = None) -> argparse.ArgumentParser:
    """Build the generic read-only resource parser."""

    parser = argparse.ArgumentParser(
        prog=prog or "grafana-util resource",
        description=(
            "Read a small set of live Grafana resources through a generic "
            "read-only query surface."
        ),
        epilog=(
            "Examples:\n\n"
            "  grafana-util resource kinds\n"
            "  grafana-util resource describe\n"
            "  grafana-util resource list dashboards --profile prod\n"
            "  grafana-util resource get datasources/prom-main --profile prod --output-format yaml\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    kinds_parser = subparsers.add_parser("kinds", help="Show supported resource kinds.")
    kinds_parser.add_argument(
        "--output-format",
        choices=OUTPUT_FORMAT_CHOICES,
        default="text",
        help="Render the result as text, table, json, yaml, or interactive.",
    )

    describe_parser = subparsers.add_parser(
        "describe", help="Describe the supported resource selectors and endpoints."
    )
    describe_parser.add_argument(
        "kind",
        nargs="?",
        choices=tuple(SUPPORTED_RESOURCE_KIND_INFO),
        default=None,
        help="Optional resource kind to describe.",
    )
    describe_parser.add_argument(
        "--output-format",
        choices=OUTPUT_FORMAT_CHOICES,
        default="text",
        help="Render the result as text, table, json, yaml, or interactive.",
    )

    list_parser = subparsers.add_parser("list", help="List live resource inventory.")
    list_parser.add_argument("kind", choices=tuple(SUPPORTED_RESOURCE_KIND_INFO))
    list_parser.add_argument(
        "--page-size",
        type=int,
        default=500,
        help="Dashboard search page size when listing dashboards.",
    )
    add_live_connection_args(list_parser)
    list_parser.add_argument(
        "--output-format",
        choices=OUTPUT_FORMAT_CHOICES,
        default="text",
        help="Render the result as text, table, json, yaml, or interactive.",
    )

    get_parser = subparsers.add_parser("get", help="Fetch one live resource payload.")
    get_parser.add_argument(
        "selector",
        help="Resource selector in kind/identity form, for example datasources/prom-main.",
    )
    add_live_connection_args(get_parser)
    get_parser.add_argument(
        "--output-format",
        choices=OUTPUT_FORMAT_CHOICES,
        default="text",
        help="Render the result as text, table, json, yaml, or interactive.",
    )

    return parser


def _resource_summary(kind: str) -> dict[str, Any]:
    info = SUPPORTED_RESOURCE_KIND_INFO[kind]
    return {
        "kind": kind,
        "description": info["description"],
        "listEndpoint": info["list"],
        "getEndpoint": info["get"],
    }


def kinds_command(args: argparse.Namespace) -> int:
    dump_document(
        {
            "kinds": [
                {
                    "kind": kind,
                    "description": info["description"],
                }
                for kind, info in SUPPORTED_RESOURCE_KIND_INFO.items()
            ]
        },
        args.output_format,
    )
    return 0


def describe_command(args: argparse.Namespace) -> int:
    if args.kind:
        dump_document(_resource_summary(args.kind), args.output_format)
        return 0
    dump_document(
        {"kinds": [_resource_summary(kind) for kind in SUPPORTED_RESOURCE_KIND_INFO]},
        args.output_format,
    )
    return 0


def _list_dashboards(client, page_size: int) -> list[dict[str, Any]]:
    return client.iter_dashboard_summaries(page_size)


def _list_folders(client) -> list[dict[str, Any]]:
    data = client.request_json("/api/folders")
    return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []


def _list_datasources(client) -> list[dict[str, Any]]:
    return client.list_datasources()


def _list_alert_rules(client) -> list[dict[str, Any]]:
    return client.list_alert_rules()


def _list_orgs(client) -> list[dict[str, Any]]:
    return client.list_organizations()


def list_command(args: argparse.Namespace) -> int:
    _, dashboard_client, datasource_client, alert_client, access_client = build_live_clients(
        args, config_path=args.config
    )
    if args.kind == "dashboards":
        rows = _list_dashboards(dashboard_client, int(args.page_size))
    elif args.kind == "folders":
        rows = _list_folders(dashboard_client)
    elif args.kind == "datasources":
        rows = _list_datasources(datasource_client)
    elif args.kind == "alert-rules":
        rows = _list_alert_rules(alert_client)
    elif args.kind == "orgs":
        rows = _list_orgs(access_client)
    else:
        raise ValueError("Unsupported resource kind: %s" % args.kind)
    dump_document({"kind": args.kind, "items": rows}, args.output_format)
    return 0


def _parse_selector(selector: str) -> tuple[str, str]:
    if "/" not in selector:
        raise ValueError("Resource selector must be in kind/identity form.")
    kind, identity = selector.split("/", 1)
    kind = kind.strip()
    identity = identity.strip()
    if kind not in SUPPORTED_RESOURCE_KIND_INFO:
        raise ValueError("Unsupported resource kind: %s" % kind)
    if not identity:
        raise ValueError("Resource selector identity cannot be empty.")
    return kind, identity


def get_command(args: argparse.Namespace) -> int:
    kind, identity = _parse_selector(args.selector)
    _, dashboard_client, datasource_client, alert_client, access_client = build_live_clients(
        args, config_path=args.config
    )
    if kind == "dashboards":
        payload = dashboard_client.fetch_dashboard(identity)
    elif kind == "folders":
        payload = dashboard_client.fetch_folder_if_exists(identity)
        if payload is None:
            raise ValueError("Folder not found: %s" % identity)
    elif kind == "datasources":
        payload = datasource_client.fetch_datasource_by_uid_if_exists(identity)
        if payload is None:
            raise ValueError("Datasource not found: %s" % identity)
    elif kind == "alert-rules":
        payload = alert_client.get_alert_rule(identity)
    elif kind == "orgs":
        payload = access_client.get_organization(identity)
    else:
        raise ValueError("Unsupported resource kind: %s" % kind)
    dump_document({"kind": kind, "identity": identity, "resource": payload}, args.output_format)
    return 0


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    try:
        args = parse_args(argv)
        if args.command == "kinds":
            return kinds_command(args)
        if args.command == "describe":
            return describe_command(args)
        if args.command == "list":
            return list_command(args)
        if args.command == "get":
            return get_command(args)
        raise RuntimeError("Unsupported resource command.")
    except (ValueError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
