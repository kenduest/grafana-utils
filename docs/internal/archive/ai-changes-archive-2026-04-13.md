# ai-changes-archive-2026-04-13

## 2026-04-12 - Externalize docs entry taxonomy and add handbook command maps
- Summary: added `scripts/contracts/docs-entrypoints.json` as the shared definition file for landing quick commands, jump-select command entries, and handbook command-relationship maps; replaced the hard-coded Python metadata with a validating loader in `scripts/docgen_entrypoints.py`.
- User impact: the generated docs homepage now exposes a stable first-run path panel, jump navigation includes `version` and `config profile`, and handbook pages such as dashboard show grouped subcommand relationships in both the left nav and an in-page command map.
- Validation: `make html`; `make html-check`; `make quality-docs-surface`; `python3 -m unittest -v python.tests.test_python_docgen_entrypoints python.tests.test_python_docgen_command_docs python.tests.test_python_check_docs_surface`

## 2026-04-12 - Re-scope Developer Guide as a short maintainer router
- Summary: rewrote `docs/DEVELOPER.md` into a shorter maintainer landing page, tightened `docs/internal/maintainer-quickstart.md` into the first-entry reading-order and source-of-truth map, extracted stable closure rules into `docs/internal/ai-change-closure-rules.md`, and routed the maintainer and AI-workflow docs to that shared closure contract so future routing changes update the right maintainer docs together.
- Validation: `make quality-ai-workflow`; `git diff --check`
