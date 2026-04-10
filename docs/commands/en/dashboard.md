# dashboard

## Purpose
`grafana-util dashboard` is the namespace for live dashboard workflows, local draft handling, export/import review, inspection, topology, and screenshots. The same namespace is also available as `grafana-util db`.

## When to use
Use this namespace when you need to browse live dashboards, fetch or clone a live dashboard into a local JSON draft, compare local files with Grafana, inspect export or live metadata, or publish a prepared dashboard back to Grafana. Use `dashboard sync convert raw-to-prompt` when the job is artifact repair rather than dashboard operations.

## Description
Open this page first when the work is about the full dashboard workflow rather than one isolated flag. The `dashboard` namespace brings together the tasks that usually travel together in real operator work: inventory reads, export and backup, migration between environments, staged review before apply, live inspection, topology checks, and reproducible screenshots.

If you are an SRE, Grafana operator, or responder, this page should help you decide which dashboard path to open next. If you already know the exact action, jump from here into the matching subcommand page for the concrete flags and examples.

## Workflow lanes

- **`dashboard live ...`**: browse, list, vars, fetch, clone, edit, delete, and history.
- **`dashboard draft ...`**: review, patch, serve, and publish around one local draft.
- **`dashboard sync ...`**: export, import, diff, and `convert raw-to-prompt`.
- **`dashboard analyze ...`**: summary, topology, impact, and governance checks.
- **`dashboard capture ...`**: screenshot flows for reproducible visual proof.

For single-dashboard authoring, the local draft path is:
- `dashboard live fetch` or `dashboard live clone` to start from one live dashboard
- `dashboard draft serve` to keep one or more drafts open in a local preview browser while you edit
- `dashboard draft review` to verify one draft
- `dashboard draft patch` to rewrite local metadata
- `dashboard live edit` to fetch one live dashboard into an editor with a safe local-draft default and a review-aware apply gate
- `dashboard draft publish` to replay that draft back through the import pipeline

`review`, `patch-file`, and `publish` also accept `--input -` for one wrapped or bare dashboard JSON document from standard input. Use that when an external generator already writes the dashboard JSON to stdout. `patch-file --input -` requires `--output`, and `publish --watch` is the local-file variant for repeated save-and-preview loops and does not support `--input -`.

Choose this page when the task is dashboard work but you are still deciding whether the next step is to inspect, move, review, or capture.

## Before / After

- **Before**: dashboard work is often split across UI browsing, one-off exports, local JSON edits, and ad hoc screenshot or review steps.
- **After**: the `dashboard` namespace keeps browse, inspect, move, review, and capture in one place, so you can pick the lane first and then jump to the matching subcommand.

## What success looks like

- you can tell whether the task is inspect, move, review, or capture before opening a subcommand
- inventory reads, export/import flows, and review surfaces share the same auth and bundle conventions
- screenshot and topology paths stay available when you need proof instead of only a final JSON blob

## Failure checks

- if browse output looks incomplete, verify the profile, auth flags, and target org before retrying
- if live inspect or topology output looks stale, confirm you are pointing at the current Grafana and not at an older local export
- if a result is going into automation, set `--output-format` explicitly so the downstream step knows the contract

## Key flags
- `--url`: Grafana base URL.
- `--token`, `--basic-user`, `--basic-password`: shared live Grafana credentials.
- `--profile`: load repo-local defaults from `grafana-util.yaml`.
- `--color`: control JSON color output for the namespace.

## Auth notes
- Prefer `--profile` for repeatable daily work and CI.
- Use direct Basic auth for bootstrap or admin-heavy flows.
- Token auth can be enough for scoped reads, but cross-org workflows such as `--all-orgs` are safer with admin-backed `--profile` or Basic auth.
- `dashboard sync convert raw-to-prompt` is usually offline, but it can optionally use `--profile` or live auth flags to look up datasource inventory while repairing prompt files.

## Examples
```bash
# Purpose: Inspect the dashboard namespace before choosing a lane.
grafana-util dashboard --help
```

```bash
# Purpose: Browse live dashboards from a saved profile.
grafana-util dashboard live browse --profile prod
```

```bash
# Purpose: Browse a local Grafana instance with explicit credentials.
grafana-util dashboard live browse --url http://localhost:3000 --basic-user admin --basic-password admin
```

```bash
# Purpose: Convert a legacy dashboard export into prompt-friendly JSON.
grafana-util dashboard sync convert raw-to-prompt --input-file ./legacy/cpu-main.json --profile prod --org-id 2
```

```bash
# Purpose: Review one generated dashboard from standard input before mutation.
jsonnet dashboards/cpu.jsonnet | grafana-util dashboard draft review --input - --output-format json
```

```bash
# Purpose: Watch one local draft file and rerun publish dry-run after each save.
grafana-util dashboard draft publish --url http://localhost:3000 --basic-user admin --basic-password admin --input ./drafts/cpu-main.json --dry-run --watch
```

```bash
# Purpose: Open one local dashboard draft in the local preview server.
grafana-util dashboard draft serve --input ./drafts/cpu-main.json --port 18080 --open-browser
```

```bash
# Purpose: Pull one live dashboard into an external editor and keep the result as a local draft by default.
grafana-util dashboard live edit --profile prod --dashboard-uid cpu-main --output ./drafts/cpu-main.edited.json
```

```bash
# Purpose: Analyze live dashboard governance data for downstream review.
grafana-util dashboard analyze summary --url http://localhost:3000 --token "$GRAFANA_API_TOKEN" --output-format governance
```

```bash
# Purpose: Open the interactive analysis workbench for a live dashboard.
grafana-util dashboard analyze summary --url http://localhost:3000 --basic-user admin --basic-password admin --interactive
```

## Related commands

### Browse and Inventory

- [dashboard browse](./dashboard-browse.md)
- [dashboard list](./dashboard-list.md)
- [dashboard fetch-live](./dashboard-fetch-live.md)
- [dashboard analyze (live)](./dashboard-analyze-live.md)
- [dashboard analyze (local)](./dashboard-analyze-export.md)
- [dashboard list-vars](./dashboard-list-vars.md)

### Move

- [dashboard clone-live](./dashboard-clone-live.md)
- [dashboard export](./dashboard-export.md)
- [dashboard import](./dashboard-import.md)
- [migrate dashboard raw-to-prompt](./migrate-dashboard-raw-to-prompt.md)
- [dashboard patch-file](./dashboard-patch-file.md)

### Author

- [dashboard serve](./dashboard-serve.md)
- [dashboard edit-live](./dashboard-edit-live.md)

### Review Before Mutate

- [dashboard diff](./dashboard-diff.md)
- [dashboard review](./dashboard-review.md)
- [dashboard publish](./dashboard-publish.md)
- [dashboard delete](./dashboard-delete.md)
- [dashboard governance-gate](./dashboard-governance-gate.md)
- [dashboard topology](./dashboard-topology.md)
- [dashboard impact](./dashboard-impact.md)

### History

- [dashboard history](./dashboard-history.md)

### Capture

- [dashboard screenshot](./dashboard-screenshot.md)
