# `grafana-util alert`

## Purpose

Run the alerting command surface for exporting, importing, diffing, planning, applying, deleting, authoring, and listing Grafana alert resources.

## When to use

- Export local alert bundles from Grafana.
- Import or diff alert bundles against live Grafana state.
- Build and apply a reviewed alert management plan.
- Author staged rules, contact points, routes, and templates.
- List live alert rules, contact points, mute timings, and templates.

## Description
Open this page when the work is about Grafana alerting as a full workflow, not just one command. The `alert` namespace covers inventory, local authoring, diff and review, and the plan/apply path that teams usually need before changing production alert resources.

This is the right entrypoint for SREs, platform operators, and anyone who wants to understand how alert rules, notification routing, and contact-point changes fit together before diving into one exact subcommand.

## Workflow lanes

- **Inspect**: list-rules, list-contact-points, list-mute-timings, and list-templates.
- **Move**: export, import, add-rule, clone-rule, add-contact-point, set-route, new-rule, new-contact-point, and new-template.
- **Review Before Mutate**: diff, plan, apply, and preview-route.

Choose this page when alert work spans rules, routes, contact points, or templates and you want the workflow before the flags.

## Before / After

- **Before**: alert work is often scattered across rule editors, export scripts, and route tweaks without one grouped path from inventory to reviewed apply.
- **After**: the `alert` namespace keeps inventory, authoring, diff, planning, and apply in one place so you can read first, then change.

## What success looks like

- you can tell whether the task belongs to inspect, move, or review-before-mutate before you open a subcommand
- a plan or export can move through review without losing routing context
- the same alert flow can be repeated in CI or during incident follow-up

## Failure checks

- if an inventory command returns less than expected, confirm whether the auth scope is wide enough for the org or folder you need
- if a review or apply step behaves strangely, inspect the alert plan JSON before assuming the CLI is wrong
- if the result is going to automation, set `--output-format` explicitly so the downstream step knows the contract

## Key flags

- `--profile`, `--url`, `--token`, `--basic-user`, `--basic-password`
- `--prompt-password`, `--prompt-token`, `--timeout`, `--verify-ssl`
- Use the nested subcommands for `export`, `import`, `diff`, `plan`, `apply`, `delete`, `add-rule`, `clone-rule`, `add-contact-point`, `set-route`, `preview-route`, `new-rule`, `new-contact-point`, `new-template`, `list-rules`, `list-contact-points`, `list-mute-timings`, and `list-templates`.

## Auth notes

- Prefer `--profile` for normal alert review and apply loops.
- Use Basic auth when you need broader org visibility or admin-backed inventory.
- Token auth works best for scoped single-org reads or automation where the token permissions are already well understood.

## Examples

```bash
# Purpose: Inspect alert inventory before choosing a lane.
grafana-util alert list-rules --profile prod --json
```

```bash
# Purpose: Export alert resources for review or migration.
grafana-util alert export --url http://localhost:3000 --basic-user admin --basic-password admin --output-dir ./alerts --overwrite
```

```bash
# Purpose: Preview the route shape before mutating live alert routing.
grafana-util alert preview-route --url http://localhost:3000 --profile prod --output-format json
```

```bash
# Purpose: Export alert resources for review or migration with token auth.
grafana-util alert export --url http://localhost:3000 --token "$GRAFANA_API_TOKEN" --output-dir ./alerts --flat
```

## Related commands

### Inspect

- [alert list-rules](./alert-list-rules.md)
- [alert list-contact-points](./alert-list-contact-points.md)
- [alert list-mute-timings](./alert-list-mute-timings.md)
- [alert list-templates](./alert-list-templates.md)

### Move

- [alert export](./alert-export.md)
- [alert import](./alert-import.md)
- [alert new-rule](./alert-new-rule.md)
- [alert add-rule](./alert-add-rule.md)
- [alert clone-rule](./alert-clone-rule.md)
- [alert new-contact-point](./alert-new-contact-point.md)
- [alert add-contact-point](./alert-add-contact-point.md)
- [alert new-template](./alert-new-template.md)
- [alert set-route](./alert-set-route.md)

### Review Before Mutate

- [alert diff](./alert-diff.md)
- [alert plan](./alert-plan.md)
- [alert apply](./alert-apply.md)
- [alert preview-route](./alert-preview-route.md)
- [alert delete](./alert-delete.md)

### Related

- [access](./access.md)
