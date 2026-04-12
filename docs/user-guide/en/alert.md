# Alert Operator Handbook

This guide is for operators who need to author alerting changes locally, review the delta before applying it, or replay legacy alert bundles without guessing at the live effect.

This guide covers `grafana-util alert` as an operator workflow for alert desired-state authoring, review-first mutation, and replay flows.

## Who It Is For

- Operators maintaining Grafana Alerting rules, routes, contact points, and templates.
- Reviewers who need to understand an alert bundle before apply.
- Teams moving alerting state through Git, review, or CI workflows.

## Primary Goals

- Build or import alert desired state without touching live Grafana first.
- Review plan output before an apply path.
- Use replay and migration flows without guessing what live resources will workspace.

## Before / After

- Before: alert changes often lived in a mixed UI and YAML path with little review context.
- After: authoring, plan output, and apply become separate checkpoints with clearer evidence.

## What success looks like

- You can tell whether you are editing desired state, reviewing a plan, or applying a real workspace.
- You can explain which part of the alerting chain is affected before touching live state.
- You can read the output and know whether the plan is safe to proceed.

## Failure checks

- If the plan output is missing a contact point or route you expected, stop and verify the staged input first.
- If the apply path would touch more than you intended, treat that as a review failure, not a rendering issue.
- If you cannot explain the alert lane you are in, return to the workflow chapter before mutating anything.

> **Operator Principle**: Change alerts deliberately through a **Plan -> Review -> Apply** cycle to prevent accidental mutations in live environments.

## 🔗 Command Pages

Need the command-by-command surface instead of the workflow guide?

- [alert](../../commands/en/alert.md)
- [alert plan](../../commands/en/alert-plan.md)
- [alert apply](../../commands/en/alert-apply.md)
- [alert list-rules](../../commands/en/alert-list-rules.md)
- [alert list-contact-points](../../commands/en/alert-list-contact-points.md)
- [alert list-mute-timings](../../commands/en/alert-list-mute-timings.md)
- [alert list-templates](../../commands/en/alert-list-templates.md)
- [full command index](../../commands/en/index.md)

---

## 🛠️ What This Area Is For

Use the alert area when the work is about Grafana alerting resources:
- **Inventory**: Inspect live rules, contact points, mute timings, and templates before you change anything.
- **Backup**: Export, import, or diff alert resources and bundles.
- **Authoring**: Build new alert configurations locally without touching live Grafana.
- **Review**: Compare your desired state against the live estate before approving changes, then apply only what you reviewed.

---

## 🚧 Workflow Boundaries (Four Lanes)

Alerting is split into four distinct operational lanes. **Do not mix these lanes.**

| Lane | Purpose | Common Commands |
| :--- | :--- | :--- |
| **Inventory** | Inspect the live alert estate before you change anything. | `list-rules`, `list-contact-points`, `list-mute-timings`, `list-templates`, `delete` |
| **Backup** | Export, import, or diff alert resources and bundles. | `export`, `import`, `diff` |
| **Authoring** | Scaffold and edit desired-state files for review/apply. | `init`, `add-rule`, `clone-rule`, `add-contact-point`, `set-route`, `preview-route`, `new-rule`, `new-contact-point`, `new-template` |
| **Review** | Build and apply a reviewed plan. | `plan`, `apply` |

---

## 📋 Authoring Desired State

Start by scaffolding a desired-state tree. This creates local files that represent your "intent".

```bash
# Initialize a desired-state tree
grafana-util alert init --desired-dir ./alerts/desired

# Add a rule to your local files (does not touch Grafana yet)
grafana-util alert add-rule \
  --desired-dir ./alerts/desired \
  --name cpu-high --folder platform-alerts \
  --receiver pagerduty-primary --threshold 80 --above --for 5m
```

---

## 🔬 Review and Apply (The Review Cycle)

Use `plan` to build a preview of the delta between your local files and live Grafana.

```bash
# Generate a plan for review
grafana-util alert plan \
  --url http://localhost:3000 \
  --basic-user admin --basic-password admin \
  --desired-dir ./alerts/desired --prune --output-format json
```

**How to Read the Plan Output:**
- **create**: Desired resource is missing in live Grafana.
- **update**: Live Grafana differs from your desired file.
- **delete**: Triggered by `--prune` when a live resource is not in your files.

**Validated Apply Step:**
Only execute after the plan has been reviewed and saved.
```bash
# Purpose: Only execute after the plan has been reviewed and saved.
grafana-util alert apply \
  --plan-file ./alert-plan-reviewed.json \
  --approve --output-format json
```

---

## 🚀 Key Commands (Full Argument Reference)

| Command | Full Example with Arguments |
| :--- | :--- |
| **List Rules** | `grafana-util alert list-rules --all-orgs --table` |
| **Init** | `grafana-util alert init --desired-dir ./alerts/desired` |
| **Export** | `grafana-util alert export --output-dir ./alerts --overwrite` |
| **Import** | `grafana-util alert import --input-dir ./alerts/raw --replace-existing --dry-run --json` |
| **Diff** | `grafana-util alert diff --diff-dir ./alerts/raw --output-format json` |
| **Plan** | `grafana-util alert plan --desired-dir ./alerts/desired --prune --output-format json` |
| **Apply** | `grafana-util alert apply --plan-file ./plan.json --approve` |
| **Set Route** | `grafana-util alert set-route --desired-dir ./alerts/desired --receiver pagerduty` |
| **Preview Route** | `grafana-util alert preview-route --desired-dir ./alerts/desired --label team=platform --severity critical` |

---

## 🔬 Validated Docker Examples

### 1. Alert Plan Excerpt
```bash
# Purpose: 1. Alert Plan Excerpt.
grafana-util alert plan --desired-dir ./alerts/desired --prune --output-format json
```
**Output Excerpt:**
```json
{
  "summary": {
    "create": 1,
    "update": 2,
    "delete": 1,
    "noop": 0,
    "blocked": 0
  }
}
```

### 2. Route Preview
Verify your routing logic locally before applying.
```bash
# Purpose: Verify your routing logic locally before applying.
grafana-util alert preview-route --desired-dir ./alerts/desired --label team=platform --severity critical
```
**Output Excerpt:**
```json
{
  "input": { "labels": { "team": "platform" }, "severity": "critical" },
  "matches": []
}
```
*Note: A blank match list means the contract was evaluated successfully, not necessarily that a live alert exists.*

---
[⬅️ Previous: Datasource Management](datasource.md) | [🏠 Home](index.md) | [➡️ Next: Access Management](access.md)
