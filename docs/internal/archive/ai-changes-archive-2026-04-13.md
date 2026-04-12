# ai-changes-archive-2026-04-13

## 2026-04-12 - Externalize docs entry taxonomy and add handbook command maps
- Summary: added `scripts/contracts/docs-entrypoints.json` as the shared definition file for landing quick commands, jump-select command entries, and handbook command-relationship maps; replaced the hard-coded Python metadata with a validating loader in `scripts/docgen_entrypoints.py`.
- User impact: the generated docs homepage now exposes a stable first-run path panel, jump navigation includes `version` and `config profile`, and handbook pages such as dashboard show grouped subcommand relationships in both the left nav and an in-page command map.
- Validation: `make html`; `make html-check`; `make quality-docs-surface`; `python3 -m unittest -v python.tests.test_python_docgen_entrypoints python.tests.test_python_docgen_command_docs python.tests.test_python_check_docs_surface`

## 2026-04-12 - Re-scope Developer Guide as a short maintainer router
- Summary: rewrote `docs/DEVELOPER.md` into a shorter maintainer landing page, tightened `docs/internal/maintainer-quickstart.md` into the first-entry reading-order and source-of-truth map, extracted stable closure rules into `docs/internal/ai-change-closure-rules.md`, and routed the maintainer and AI-workflow docs to that shared closure contract so future routing changes update the right maintainer docs together.
- Validation: `make quality-ai-workflow`; `git diff --check`

## 2026-04-12 - Remove legacy CLI compatibility
- Summary: removed the binary-level legacy command hint layer, deleted the legacy help module, removed unused old alert grouping schema from `cli.rs`, removed `legacy_replacements` support from the docs-surface contract/checker, kept `grafana-util alert --help` focused on real flat commands, and updated colored help rendering so option entries, inline `--flag` references, and example captions are highlighted.
- Tests: updated CLI tests to assert removed roots and old alert grouped forms are rejected through the normal Clap path, are not intercepted by custom help preflight, and colored contextual help highlights option entries, inline flags, and example captions across dashboard, alert, datasource, and profile help.
- Test Run: `cargo fmt --manifest-path rust/Cargo.toml --all`; `cargo test --manifest-path rust/Cargo.toml --quiet cli_rust_tests -- --test-threads=1`; `cargo fmt --manifest-path rust/Cargo.toml --all --check`; `make man`; `make html`; `make man-check`; `make html-check`; `make quality-docs-surface`; `make quality-ai-workflow`; `python3 -m json.tool scripts/contracts/command-surface.json`; `python3 -m json.tool scripts/contracts/command-reference-index.json`.
- Validation: manually checked `grafana-util --color always das ex --help` through `cargo run --manifest-path rust/Cargo.toml --quiet --bin grafana-util -- ... | cat -v` and confirmed option entries, aliases, and inline flags emit highlight ANSI.
- Impact: `rust/src/bin/grafana-util.rs`, `rust/src/cli.rs`, `rust/src/cli_help.rs`, `rust/src/cli_help_examples.rs`, `rust/src/cli_help/grouped_specs.rs`, `rust/src/cli_rust_tests.rs`, `scripts/check_docs_surface.py`, `scripts/contracts/command-surface.json`, `scripts/contracts/command-reference-index.json`, `docs/commands/{en,zh-TW}/`, `docs/internal/ai-status.md`.
- Rollback/Risk: old commands now receive standard parser errors with no compatibility mapping; rollback would restore the deleted legacy hint module and contract field.
- Follow-up: none.
