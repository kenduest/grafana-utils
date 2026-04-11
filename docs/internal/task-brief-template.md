# Task Brief Template

Use this template when you want to hand a repo task to an AI agent.

Copy it into:

- a chat prompt
- an issue body
- a PR description
- a local scratch note

Repo-owned copies also live in:

- `.github/ISSUE_TEMPLATE/ai-task-brief.md`
- `.github/PULL_REQUEST_TEMPLATE.md`

Keep it short. The goal is to make the task precise enough that the agent can
find the right source-of-truth files and run the right validation.

## Template

```text
Goal:
- What should change?

Touched Surface:
- Which subsystem, command family, docs lane, or build lane is in scope?

Constraints:
- What must not change?
- What compatibility or workflow rule must stay intact?

Owned Layer:
- Which layer owns the change: runtime, parser/help, contract, docs, generated docs, or trace?

Source-Of-Truth Files:
- Which code, docs, or contract files own this change?

Contract Impact:
- Does this change alter a stable shape, compatibility rule, or generated artifact contract?
- If yes, which current contract doc owns the rule?

Expected Companion Updates:
- Which docs, tests, generated outputs, spec docs, or trace docs should change too?

Test Strategy:
- Which narrow checks should pass first?
- Which behavior-level or regression tests must change?
- Which broader checks are required if the change crosses subsystem boundaries?

Docs Impact Matrix:
- Public handbook/manual:
  - Does this task change stable workflow, intent, user journeys, or decision tables?
- Command reference:
  - Does this task change command names, flags, examples, or per-command help text?
- Generated docs:
  - Does this task require regenerating man pages, HTML docs, or other derived output?
- Internal docs:
  - Does this task change maintainer contracts, architecture notes, or routing?
- Trace docs:
  - Does this task need a concise status or change-log update?
- If any of the above are yes, what is the source doc or generator that must change first?

Validation:
- Which exact commands should be run to confirm the narrow and broader checks?

Review Shape:
- Solo: diff review
- Collaborative: PR review
```

## Example

```text
Goal:
- Add one dashboard export flag for flat output naming.

Touched Surface:
- dashboard CLI
- command reference docs

Constraints:
- Keep existing raw export contract intact.
- Do not change dashboard import semantics.

Owned Layer:
- parser/help + command-reference docs

Source-Of-Truth Files:
- rust/src/dashboard/
- docs/commands/en/dashboard-export.md
- docs/commands/zh-TW/dashboard-export.md

Contract Impact:
- None; existing dashboard export shape stays intact.

Expected Companion Updates:
- focused parser/help tests
- command docs
- regenerated man/html output if source docs changed

Test Strategy:
- parser/help assertions for the export command
- command-doc smoke check if wording changes
- broader Rust tests only if the change crosses dashboard runtime paths

Docs Impact Matrix:
- Public handbook/manual: no change
- Command reference: update wording for the new flag
- Generated docs: regenerate man/html after changing command-reference source docs
- Internal docs: no change
- Trace docs: no change

Validation:
- cd rust && cargo test --quiet
- make man-check
- make html-check

Review Shape:
- Solo: diff review
```
