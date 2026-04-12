# AI Change Closure Rules

Use this note when an AI-assisted change crosses source-of-truth, maintainer
routing, or generated-doc boundaries.

This file keeps the closure rules that should stay stable even when the higher
level workflow note is rewritten or reorganized.

## Companion Update Rules

When new information enters the repo, update the owning layer instead of only
editing the first file touched.

Expected companion updates:

- runtime behavior change:
  - code, focused tests, and the public docs or help text that describe the
    behavior
- contract change:
  - code, focused tests, and the owning current contract doc in
    `docs/internal/`
- docs-generator change:
  - source docs or generator code, regenerated outputs when required, the
    generated-docs architecture or playbook if the workflow changed, and
    `scripts/contracts/command-surface.json` when public command paths or docs
    routing changed
- maintainer-routing change:
  - the owning internal maintainer docs, not just one local note

## Maintainer Routing Closure

When a change affects maintainer routing, keep the maintainer docs contract
closed in the same patch.

Use this split:

- `docs/DEVELOPER.md`
  - short maintainer landing page by concern
- `docs/internal/maintainer-quickstart.md`
  - first-entry reading order and source-of-truth map
- `docs/internal/maintainer-role-map.md`
  - persona-based routing
- `docs/internal/contract-doc-map.md`
  - contract and policy routing

Apply these closure rules:

- if repo entry routing changed:
  - update `docs/DEVELOPER.md` and `docs/internal/maintainer-quickstart.md`
- if maintainer persona routing changed:
  - update `docs/internal/maintainer-role-map.md`
- if a contract or policy doc moved or was renamed:
  - update `docs/internal/contract-doc-map.md` and every router that links to it
- if AI workflow routing changed:
  - update `docs/internal/ai-workflow-note.md`, and update the routers only if
    the entry route changed

Do not leave routing knowledge half-updated across those files. If the new
entry path, maintainer persona map, or contract-doc route changed, update the
owning router in the same patch rather than expecting later cleanup.

## Source-Of-Truth Rules

Use these boundaries consistently:

- `rust/src/` is the maintained implementation surface
- `python/grafana_utils/` is legacy reference unless the task is explicitly in
  scope there
- `docs/user-guide/{en,zh-TW}/` is the handbook source layer
- `docs/commands/{en,zh-TW}/` is the command-reference source layer
- `docs/man/` and `docs/html/` are generated artifacts
- `docs/internal/*.md` should stay split by purpose:
  - summary in `docs/DEVELOPER.md`
  - spec in the dedicated current contract or architecture docs
  - trace in `docs/internal/ai-status.md` and `docs/internal/ai-changes.md`

If an AI agent edits a generated artifact without updating its source layer, the
change is incomplete unless the task is explicitly about generated output
debugging.

## Stop And Ask Conditions

The agent should not guess when:

- two current contract docs appear to disagree
- a change would redefine a stable field or compatibility rule
- the task conflicts with unrelated user changes already in the worktree
- generated docs and source docs disagree, but the intended truth source is not
  obvious
- the narrow validation path fails in unrelated parts of the repo and the risk
  is no longer local
