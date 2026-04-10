# advanced

## Purpose
`grafana-util advanced` is the expert-facing namespace for domain-specific workflows.

## When to use
Use this namespace once you already know the subsystem you need, such as dashboard import, alert authoring, datasource diff, or access administration.

## Description
The `advanced` tree preserves the full domain depth of `grafana-util` without making new users learn every lane on the first screen. It is the preferred canonical home for domain-heavy workflows, while older top-level roots remain available as compatibility paths.

## Subcommands

- `advanced dashboard ...`
- `advanced alert ...`
- `advanced datasource ...`
- `advanced access ...`

## Examples
```bash
grafana-util advanced dashboard sync import --input-dir ./dashboards/raw --dry-run --table
```

```bash
grafana-util advanced alert author route preview --desired-dir ./alerts/desired --label team=sre --severity critical
```

```bash
grafana-util advanced datasource diff --diff-dir ./datasources --input-format inventory
```

```bash
grafana-util advanced access user diff --diff-dir ./access-users --scope global
```

## Related commands

- [export](./export.md)
- [change](./change.md)
- [dashboard](./dashboard.md)
- [alert](./alert.md)
- [datasource](./datasource.md)
- [access](./access.md)
