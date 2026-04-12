# ai-status.md

Current AI-maintained status only.

- Older trace history moved to [`archive/ai-status-archive-2026-03-24.md`](/Users/kendlee/work/grafana-utils/docs/internal/archive/ai-status-archive-2026-03-24.md).
- Detailed 2026-03-27 entries moved to [`archive/ai-status-archive-2026-03-27.md`](/Users/kendlee/work/grafana-utils/docs/internal/archive/ai-status-archive-2026-03-27.md).
- Detailed 2026-03-28 task notes were condensed into [`archive/ai-status-archive-2026-03-28.md`](/Users/kendlee/work/grafana-utils/docs/internal/archive/ai-status-archive-2026-03-28.md).
- Detailed 2026-03-29 through 2026-03-31 entries moved to [`archive/ai-status-archive-2026-03-31.md`](/Users/kendlee/work/grafana-utils/docs/internal/archive/ai-status-archive-2026-03-31.md).
- Detailed 2026-04-01 through 2026-04-12 entries moved to [`archive/ai-status-archive-2026-04-12.md`](/Users/kendlee/work/grafana-utils/docs/internal/archive/ai-status-archive-2026-04-12.md).
- Keep this file short and current. Additive historical detail belongs in `docs/internal/archive/`.

## 2026-04-12 - Re-scope Developer Guide as a maintainer landing page
- State: Done
- Scope: `docs/DEVELOPER.md`, `docs/internal/maintainer-quickstart.md`, `docs/internal/ai-workflow-note.md`, `docs/internal/ai-change-closure-rules.md`, `docs/internal/task-brief-template.md`, `docs/internal/README.md`, plus the repo-maintained AI trace files required by the maintainer-doc workflow gate.
- Current Update: rewrote `docs/DEVELOPER.md` from an oversized mixed router/policy page into a shorter maintainer landing page; tightened `maintainer-quickstart` into the first-entry reading-order and source-of-truth map; moved stable closure rules into a dedicated `ai-change-closure-rules.md`; and routed both the maintainer docs and the AI workflow note to that stable closure file.
- Result: the maintainer entrypoint is now closer to its intended role, the quickstart no longer competes with it as a second guide, and future maintainer-routing changes have both a reusable closure contract and visible router links that reduce dropped updates across maintainer docs.

## 2026-04-12 - Add machine-readable docs surface contract and verifier
- State: Done
- Scope: `scripts/contracts/command-surface.json`, `scripts/check_docs_surface.py`, `Makefile`, `AGENTS.md`, maintainer routing docs, generated-doc playbook/architecture docs, and the affected public docs that still advertised removed roots or stale alert paths.
- Current Update: added a machine-readable command/docs synchronization contract, a docs surface verifier that checks shell fenced examples and local links against the Rust CLI, and wired that check into the repo Make targets; updated AI-facing routing so future agents know this contract is mandatory when public command paths or help support change.
- Result: public docs now have an enforceable sync point with the CLI surface, and future docs drift should fail fast through `make quality-docs-surface` instead of waiting for manual review.

## 2026-04-12 - Externalize docs entry taxonomy and handbook command maps
- State: Done
- Scope: `scripts/contracts/docs-entrypoints.json`, `scripts/docgen_entrypoints.py`, `scripts/generate_command_html.py`, handbook HTML navigation, and landing/jump navigation output.
- Current Update: moved landing quick commands, jump-select command entries, and handbook command-relationship maps into a machine-readable definition file, then updated the HTML generator to load and validate that data instead of carrying the navigation content in Python constants.
- Result: docs-entry content can now evolve by editing a data file while Python stays responsible for validation and rendering, and handbook pages such as dashboard now expose the command family and subcommand relationships directly in the left nav and page intro.

## 2026-04-12 - Split production Rust modules and clean root artifacts
- State: Done
- Scope: `rust/src/sync/{mod.rs,cli_args.rs,dispatch.rs,output.rs,cli.rs}`, `rust/src/alert_cli_*`, `rust/src/alert_support_*`, `rust/src/dashboard/{browse_input*,history*}`, `rust/src/datasource_{export,import}_*`, `rust/audit-home.edited.json`, `rust/smoke-prom-only.edited.json`, and `rust/x`.
- Current Update: split the sync, alert CLI, alert support, dashboard history, dashboard browse, and datasource import/export Rust surfaces into smaller owning modules, then removed stale tracked root artifacts from `rust/`.
- Result: the Rust architecture lint no longer needs a `sync/mod.rs` known-debt carve-out, and the current hotspot list is narrower and closer to the repo's actual remaining ownership gaps.

## 2026-04-12 - Add docs architecture guardrails for manual stability
- State: Done
- Scope: `docs/internal/docs-architecture-guardrails.md`, `docs/DEVELOPER.md`, `docs/internal/README.md`, `docs/internal/maintainer-quickstart.md`, `docs/internal/task-brief-template.md`, and `docs/internal/ai-workflow-note.md`.
- Current Update: added docs-layer guardrails that separate handbook/manual intent from command-reference syntax, keep generated docs derived, and route trace docs and internal docs to their own responsibilities; task briefs now use a docs-impact matrix.
- Result: future code changes should update command docs first, keep manuals on stable user journeys and decision tables, and avoid forcing handbook/manual rewrites for every CLI detail change.

## 2026-04-12 - Tighten AI workflow task brief and trace rules
- State: Done
- Scope: `docs/internal/task-brief-template.md`, `docs/internal/ai-workflow-note.md`, `docs/internal/ai-status.md`, and `docs/internal/ai-changes.md`.
- Current Update: added owned-layer, source-of-truth, contract impact, test strategy, and generated-doc impact fields to the task brief template; added an architecture consistency pass to the AI workflow note.
- Result: future AI-assisted changes have a clearer intake shape and a required check against current guardrails before large-file or architecture edits.

## 2026-04-12 - Split CLI dispatch and domain runtime spines
- State: Done
- Scope: Rust unified CLI dispatch, help preflight, dashboard runtime, datasource runtime, and domain help text ownership.
- Current Update: `cli.rs` now owns parser topology while `cli_dispatch.rs` owns parsed command routing. The binary has one unified help preflight, including dashboard leaf and `--help-full` paths. Dashboard and datasource execution moved behind `dashboard/command_runner.rs` and `datasource_runtime.rs`.
- Result: future command work has clearer extension points: parser shape in `cli.rs`, dispatch decisions in `cli_dispatch.rs`, help routing in `cli_help/routing.rs`, and domain execution in the owning runtime module.

## 2026-04-12 - Split CLI help architecture by responsibility
- State: Done
- Scope: `rust/src/cli_help.rs`, `rust/src/cli_help/{grouped.rs,grouped_specs.rs,routing.rs,schema.rs,legacy.rs}`, CLI help tests, and AI workflow notes.
- Current Update: `cli_help.rs` is now a facade over grouped help specs/rendering, contextual help routing, schema help, and legacy command hints.
- Result: command-entry help remains behaviorally compatible while grouped entrypoints, schema-help routing, and legacy hints no longer compete inside one oversized file.

## 2026-04-12 - Support unique-prefix CLI subcommands
- State: Done
- Scope: Rust parser/help canonicalization and CLI tests.
- Current Update: enabled Clap subcommand inference and wired the custom help preflight through clap-tree canonicalization.
- Result: unique prefixes such as `dashb` and `dashboard li` resolve to canonical commands; ambiguous prefixes such as `da` stay on Clap's error path.
