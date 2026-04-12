# Operator Handbook

## Language

- English handbook: [current page](./index.md)
- Traditional Chinese handbook: [繁體中文手冊](../zh-TW/index.md)
- English command reference: [Command Reference](../../commands/en/index.md)
- Traditional Chinese command reference: [指令參考](../../commands/zh-TW/index.md)

---

This handbook is the reading path for `grafana-util`. Start here when you want the workflow first and the exact syntax later. If you already know the command family or flag you need, switch to the command reference instead of forcing the handbook to do that job.

## How to read this handbook

1. Start with what the tool is for.
2. Read the getting started chapter.
3. Choose the role or task chapter that matches your work.
4. Switch to the command reference when you need exact subcommands or flags.

## Book map

### Part 1: Start here

- [What grafana-util is for](what-is-grafana-util.md)
- [Getting Started](getting-started.md)

### Part 2: Role paths

- [New User Path](role-new-user.md)
- [SRE / Ops Path](role-sre-ops.md)
- [Automation / CI Path](role-automation-ci.md)

### Part 3: Operation surfaces

- [Workspace Review & Status](status-workspace.md)
- [Dashboard Management](dashboard.md)
- [Data source Management](datasource.md)
- [Alerting Governance](alert.md)
- [Access Management](access.md)

### Part 4: Design principles

- [Architecture & Design Principles](architecture.md)

### Part 5: Reference and troubleshooting

- [Practical Scenarios](scenarios.md)
- [Best Practices & Recipes](recipes.md)
- [Technical Reference](reference.md)
- [Troubleshooting & Glossary](troubleshooting.md)

## Reading by role

- New user: start with [What grafana-util is for](what-is-grafana-util.md), then [New User Path](role-new-user.md), then [Getting Started](getting-started.md).
- SRE / operator: start with [SRE / Ops Path](role-sre-ops.md), then [Workspace Review & Status](status-workspace.md), [Dashboard Management](dashboard.md), [Data source Management](datasource.md), and [Troubleshooting & Glossary](troubleshooting.md).
- Identity / access administrator: start with [Access Management](access.md), then [Technical Reference](reference.md), then the [Command Reference](../../commands/en/index.md).
- Automation / CI owner: start with [Automation / CI Path](role-automation-ci.md), then [Technical Reference](reference.md), then the [Command Reference](../../commands/en/index.md).
- Maintainer / architect: start with [Architecture & Design Principles](architecture.md), then [Developer guide](../../DEVELOPER.md), then the internal docs under [docs/internal/README.md](../../internal/README.md).

## Reading notes

- The footer `Next` and `Previous` links are the intended way to continue chapter by chapter.
- Use the handbook for process and context; use the command reference for exact syntax.
- When you need terminal-shaped lookup, open the command reference or the manpage instead of reconstructing flags from memory.
