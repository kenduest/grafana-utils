# dashboard analyze-live

## Purpose
Analyze live Grafana dashboards via a temporary raw-export snapshot.

## When to use
Use this when you need the same analysis views as `analyze-export`, but sourced from live Grafana instead of a local export tree.

## Key flags
- `--page-size`: dashboard search page size.
- `--concurrency`: maximum parallel fetch workers.
- `--org-id`: analyze one explicit Grafana org.
- `--all-orgs`: analyze across visible orgs.
- `--report`, `--output-format`, `--output-file`, `--interactive`, `--no-header`: output controls.
- `--progress`: show fetch progress.

## Examples
```bash
# Purpose: Analyze live Grafana dashboards via a temporary raw-export snapshot.
grafana-util dashboard analyze-live --url http://localhost:3000 --basic-user admin --basic-password admin --output-format governance-json
```

```bash
# Purpose: Analyze live Grafana dashboards via a temporary raw-export snapshot.
grafana-util dashboard analyze-live --url http://localhost:3000 --basic-user admin --basic-password admin --interactive
```

## Related commands
- [dashboard analyze-export](./dashboard-analyze-export.md)
- [dashboard list-vars](./dashboard-list-vars.md)
- [dashboard governance-gate](./dashboard-governance-gate.md)
