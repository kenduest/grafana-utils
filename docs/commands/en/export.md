# export

## Purpose
`grafana-util export` is the task-first surface for common backup and local inventory capture jobs.

## When to use
Use this namespace when the job is straightforward export or backup and you do not want to start from a domain-heavy tree.

## Description
`export` is intentionally narrow. It wraps the existing domain export flows without changing their underlying behavior. This keeps first-run usage simple while preserving the deeper `advanced` and compatibility trees for expert work.

## Subcommands

- `export dashboard`
- `export alert`
- `export datasource`
- `export access user`
- `export access org`
- `export access team`
- `export access service-account`

## Examples
```bash
grafana-util export dashboard --output-dir ./dashboards --overwrite
```

```bash
grafana-util export alert --output-dir ./alerts --overwrite
```

```bash
grafana-util export datasource --output-dir ./datasources
```

```bash
grafana-util export access service-account --output-dir ./access-service-accounts
```

## Related commands

- [advanced](./advanced.md)
- [dashboard export](./dashboard-export.md)
- [alert export](./alert-export.md)
- [datasource export](./datasource-export.md)
- [access](./access.md)
