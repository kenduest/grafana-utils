# ai-status-archive-2026-04-13

## 2026-04-12 - Infer unique long option prefixes
- State: Done
- Scope: `rust/src/cli.rs`, `rust/src/access/cli_defs.rs`, CLI parser tests, and AI trace docs.
- Baseline: unique-prefix matching worked for subcommands, but long options such as `--all-o` only produced a suggestion for `--all-orgs` instead of resolving the unique match.
- Current Update: enabled Clap unique long-argument inference on the unified root parser and access parser, with tests for inferred unique prefixes and rejected ambiguous prefixes.
- Result: `grafana-util access user list --all-o --tab` now parses as `--all-orgs --table`; ambiguous or invalid long prefixes still stay on Clap's error path.

## 2026-04-12 - Add flat CLI help inventory
- State: Done
- Scope: unified help routing, CLI help tests, command-surface contract, command reference index docs, and AI trace docs.
- Baseline: grouped `--help` and supported `--help-full` paths exist, but no root-level flat inventory lists every public command path with purpose text.
- Current Update: added `grafana-util --help-flat` as a pre-parse help path that renders visible Clap command paths with group/command kind and purpose.
- Result: root flat help now lists public command paths across status, export, dashboard, datasource, alert, access, workspace, and config with operator-facing purpose text; access leaf command purposes no longer leak Args struct documentation.
