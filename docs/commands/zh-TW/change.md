# `grafana-util change`

## Root

用途：以先審核、再套用為主的同步工作流程，支援可選的 live Grafana 擷取與套用路徑。

適用時機：當你需要整理 desired resources、比對 live state、檢視 plan、套用已審核的 plan、稽核 drift，或產生 bundle 與 promotion 的 preflight 文件時。

說明：如果你的團隊走的是先審核、再套用的變更流程，先看這一頁最合適。`change` 指令群組把 summary、preflight、plan、review、audit 與 apply 都放在同一個控制面下，方便你先看懂整條流程，再決定要執行哪個精確子命令。

主要旗標：root 指令本身只是指令群組；主要操作旗標都在子指令上。常見的工作流程輸入包含 `--desired-file`、`--plan-file`、`--live-file`、`--fetch-live`、`--approve`、`--execute-live`、`--source-bundle`、`--target-inventory`、`--availability-file`、`--mapping-file` 和 `--output-format`。

### 給 CI / 腳本用的 JSON contract

如果你要用 `change` 系列輸出給 CI、腳本或外部系統判斷，請先用 `kind` 與 `schemaVersion` 當成 contract 識別，再讀後面的欄位。

CLI 內建快速查詢：

- `grafana-util change --help-schema`
- `grafana-util change summary --help-schema`
- `grafana-util change plan --help-schema`
- `grafana-util change apply --help-schema`

| 指令 | 輸出 kind | 主要 top-level 欄位 |
| --- | --- | --- |
| `change summary --output-format json` | `grafana-utils-sync-summary` | `kind`、`schemaVersion`、`toolVersion`、`summary`、`resources` |
| `change plan --output-format json` | `grafana-utils-sync-plan` | `kind`、`schemaVersion`、`toolVersion`、`dryRun`、`reviewRequired`、`reviewed`、`allowPrune`、`summary`、`alertAssessment`、`operations`、`traceId`、`stage`、`stepIndex`、`parentTraceId` |
| `change review --output-format json` | `grafana-utils-sync-plan` | 和 plan 相同，但多了 `reviewedBy`、`reviewedAt`、`reviewNote`，而且 lineage 會改成 `stage=review` |
| `change apply --output-format json` | `grafana-utils-sync-apply-intent` | `kind`、`schemaVersion`、`toolVersion`、`mode`、`reviewed`、`reviewRequired`、`allowPrune`、`approved`、`summary`、`alertAssessment`、`operations`、可選 `preflightSummary`、可選 `bundlePreflightSummary`、`appliedBy`、`appliedAt`、`approvalReason`、`applyNote`、`traceId`、`stage`、`stepIndex`、`parentTraceId` |
| `change apply --execute-live --output-format json` | live apply result | `mode`、`appliedCount`、`results` |
| `change audit --output-format json` | `grafana-utils-sync-audit` | `kind`、`schemaVersion`、`toolVersion`、`summary`、`currentLock`、`baselineLock`、`drifts` |
| `change preflight --output-format json` | `grafana-utils-sync-preflight` | `kind`、`schemaVersion`、`toolVersion`、`summary`、`checks` |
| `change assess-alerts --output-format json` | `grafana-utils-alert-sync-plan` | `kind`、`schemaVersion`、`toolVersion`、`summary`、`alerts` |
| `change bundle-preflight --output-format json` | `grafana-utils-sync-bundle-preflight` | `kind`、`schemaVersion`、`summary`、`syncPreflight`、`alertArtifactAssessment`、`secretPlaceholderAssessment`、`providerAssessment` |
| `change promotion-preflight --output-format json` | `grafana-utils-sync-promotion-preflight` | `kind`、`schemaVersion`、`toolVersion`、`summary`、`bundlePreflight`、`mappingSummary`、`checkSummary`、`handoffSummary`、`continuationSummary`、`checks`、`resolvedChecks`、`blockingChecks` |

補充：

- `change apply` 有兩種 JSON shape。沒有 `--execute-live` 時，回的是 staged apply intent；有 `--execute-live` 時，回的是 live 執行結果。
- `change summary`、`change plan`、`change review`、`change apply` 都有 `summary`，但裡面的聚合欄位會隨 stage 不同而改變。
- `change bundle` 不用 `--output-format` 來挑格式；它是用 `--output-file` 把 source bundle 寫到檔案。

範例：

```bash
# 用途：Root。
grafana-util change summary --desired-file ./desired.json
```

```bash
# 用途：Root。
grafana-util change plan --desired-file ./desired.json --fetch-live --profile prod
```

```bash
# 用途：Root。
grafana-util change apply \
  --plan-file ./sync-plan-reviewed.json \
  --approve \
  --execute-live \
  --url http://localhost:3000 \
  --basic-user admin \
  --basic-password admin
```

```bash
# 用途：Root。
grafana-util change plan \
  --desired-file ./desired.json \
  --fetch-live \
  --url http://localhost:3000 \
  --token "$GRAFANA_API_TOKEN"
```

相關指令：`grafana-util overview`、`grafana-util status`、`grafana-util snapshot`。

## `summary`

用途：彙總本機 desired 同步資源。

適用時機：當你想在規劃或套用前，先快速確認規模大小時。

主要旗標：`--desired-file`、`--output-format`。

JSON shape：

- `kind`：`grafana-utils-sync-summary`
- `schemaVersion`：目前 contract 版本
- `toolVersion`：輸出這份文件的 CLI 版本
- `summary`：聚合計數
  - `resourceCount`、`dashboardCount`、`datasourceCount`、`folderCount`、`alertCount`
- `resources`：標準化後的資源列
  - `kind`、`identity`、`title`、`managedFields`、`bodyFieldCount`、`sourcePath`

範例：

```bash
# 用途：summary。
grafana-util change summary --desired-file ./desired.json
```

```bash
# 用途：summary。
grafana-util change summary --desired-file ./desired.json --output-format json
```

相關指令：`change plan`、`change preflight`。

## `plan`

用途：根據 desired 與 live state 建立分階段的同步 plan。

適用時機：當你需要一份可供審核的 plan，確認後再標記完成或直接套用時。

主要旗標：`--desired-file`、`--live-file`、`--fetch-live`、`--org-id`、`--page-size`、`--allow-prune`、`--trace-id`、`--output-format`。

JSON shape：

- `kind`：`grafana-utils-sync-plan`
- `schemaVersion`、`toolVersion`
- staged metadata：`dryRun`、`reviewRequired`、`reviewed`、`allowPrune`
- lineage：`traceId`、`stage`、`stepIndex`、`parentTraceId`
- `summary`
  - `would_create`、`would_update`、`would_delete`、`noop`、`unmanaged`
  - `alert_candidate`、`alert_plan_only`、`alert_blocked`
- `alertAssessment`：巢狀 alert sync 摘要與 `alerts` 列表
- `operations`：每一筆 desired/live 比對結果
  - `kind`、`identity`、`title`、`action`、`reason`、`changedFields`、`managedFields`、`desired`、`live`、`sourcePath`

範例：

```bash
# 用途：plan。
grafana-util change plan --desired-file ./desired.json --live-file ./live.json
```

```bash
# 用途：plan。
grafana-util change plan \
  --desired-file ./desired.json \
  --fetch-live \
  --profile prod \
  --output-format json
```

```bash
# 用途：plan。
grafana-util change plan \
  --desired-file ./desired.json \
  --fetch-live \
  --url http://localhost:3000 \
  --basic-user admin \
  --basic-password admin \
  --allow-prune \
  --output-format json
```

```bash
# 用途：plan。
grafana-util change plan \
  --desired-file ./desired.json \
  --fetch-live \
  --url http://localhost:3000 \
  --token "$GRAFANA_API_TOKEN" \
  --allow-prune \
  --output-format json
```

相關指令：`change review`、`change apply`、`change summary`。

## `review`

用途：將分階段的同步 plan 標記為已審核。

適用時機：當 plan 已經檢視完成，且在 apply 之前需要明確的審核 token 時。

主要旗標：`--plan-file`、`--review-token`、`--reviewed-by`、`--reviewed-at`、`--review-note`、`--interactive`、`--output-format`。

JSON shape：

- 基本 shape 和 `change plan` 相同
- review state 會變成：
  - `reviewed: true`
  - `stage: review`
  - `stepIndex: 2`
- review audit 欄位：
  - `reviewedBy`
  - `reviewedAt`
  - `reviewNote`

範例：

```bash
# 用途：review。
grafana-util change review --plan-file ./sync-plan.json
```

```bash
# 用途：review。
grafana-util change review --plan-file ./sync-plan.json --review-note 'peer-reviewed' --output-format json
```

相關指令：`change plan`、`change apply`。

## `apply`

用途：根據已審核的同步 plan 產生受控的 apply intent，並可選擇直接執行到 live。

適用時機：當 plan 已經審核完成，而你準備輸出或執行 apply 步驟時。

主要旗標：`--plan-file`、`--preflight-file`、`--bundle-preflight-file`、`--approve`、`--execute-live`、`--allow-folder-delete`、`--allow-policy-reset`、`--org-id`、`--output-format`、`--applied-by`、`--applied-at`、`--approval-reason`、`--apply-note`。

JSON shape：

- 預設 `change apply --output-format json`
  - `kind`：`grafana-utils-sync-apply-intent`
  - `schemaVersion`、`toolVersion`
  - `mode: apply`
  - `reviewed`、`reviewRequired`、`allowPrune`、`approved`
  - `summary`、`alertAssessment`、`operations`
  - 可選 `preflightSummary`
  - 可選 `bundlePreflightSummary`
  - `appliedBy`、`appliedAt`、`approvalReason`、`applyNote`
  - `traceId`、`stage`、`stepIndex`、`parentTraceId`
- `change apply --execute-live --output-format json`
  - `mode: live-apply`
  - `appliedCount`
  - `results`
    - 每筆包含 `kind`、`identity`、`action`、`response`

範例：

```bash
# 用途：apply。
grafana-util change apply --plan-file ./sync-plan-reviewed.json --approve
```

```bash
# 用途：apply。
grafana-util change apply \
  --plan-file ./sync-plan-reviewed.json \
  --approve \
  --execute-live \
  --url http://localhost:3000 \
  --basic-user admin \
  --basic-password admin
```

```bash
# 用途：apply。
grafana-util change apply \
  --plan-file ./sync-plan-reviewed.json \
  --approve \
  --execute-live \
  --allow-folder-delete \
  --url http://localhost:3000 \
  --token "$GRAFANA_API_TOKEN"
```

相關指令：`change review`、`change preflight`、`change bundle-preflight`。

## `audit`

用途：比對受管 Grafana 資源的 checksum lock 與目前 live state，進行稽核。

適用時機：當你需要做 drift 檢查，或想刷新 lock snapshot 時。

主要旗標：`--managed-file`、`--lock-file`、`--live-file`、`--fetch-live`、`--org-id`、`--page-size`、`--write-lock`、`--fail-on-drift`、`--interactive`、`--output-format`。

JSON shape：

- `kind`：`grafana-utils-sync-audit`
- `schemaVersion`、`toolVersion`
- `summary`
  - `managedCount`、`baselineCount`、`currentPresentCount`、`currentMissingCount`
  - `inSyncCount`、`driftCount`、`missingLockCount`、`missingLiveCount`
- `currentLock`：目前重新建出的 lock snapshot
- `baselineLock`：既有 lock 文件，或 `null`
- `drifts`
  - `kind`、`identity`、`title`、`status`
  - `baselineStatus`、`currentStatus`
  - `baselineChecksum`、`currentChecksum`
  - `driftedFields`、`sourcePath`

範例：

```bash
# 用途：audit。
grafana-util change audit --managed-file ./desired.json --live-file ./live.json --write-lock ./sync-lock.json
```

```bash
# 用途：audit。
grafana-util change audit \
  --lock-file ./sync-lock.json \
  --fetch-live \
  --profile prod \
  --output-format json
```

```bash
# 用途：audit。
grafana-util change audit \
  --lock-file ./sync-lock.json \
  --fetch-live \
  --url http://localhost:3000 \
  --basic-user admin \
  --basic-password admin \
  --fail-on-drift \
  --output-format json
```

```bash
# 用途：audit。
grafana-util change audit \
  --lock-file ./sync-lock.json \
  --fetch-live \
  --url http://localhost:3000 \
  --token "$GRAFANA_API_TOKEN" \
  --fail-on-drift \
  --output-format json
```

相關指令：`change preflight`、`change plan`、`status live`。

## `preflight`

用途：根據 desired resources 與可選的 availability 提示，建立分階段的同步 preflight 文件。

適用時機：當你需要在規劃或套用前先做結構性門檻檢查時。

主要旗標：`--desired-file`、`--availability-file`、`--fetch-live`、`--org-id`、`--output-format`。

JSON shape：

- `kind`：`grafana-utils-sync-preflight`
- `schemaVersion`、`toolVersion`
- `summary`
  - `checkCount`、`okCount`、`blockingCount`
- `checks`
  - `kind`、`identity`、`status`、`detail`、`blocking`

範例：

```bash
# 用途：preflight。
grafana-util change preflight --desired-file ./desired.json --availability-file ./availability.json
```

```bash
# 用途：preflight。
grafana-util change preflight \
  --desired-file ./desired.json \
  --fetch-live \
  --profile prod \
  --output-format json
```

```bash
# 用途：preflight。
grafana-util change preflight \
  --desired-file ./desired.json \
  --fetch-live \
  --url http://localhost:3000 \
  --basic-user admin \
  --basic-password admin \
  --output-format json
```

```bash
# 用途：preflight。
grafana-util change preflight \
  --desired-file ./desired.json \
  --fetch-live \
  --url http://localhost:3000 \
  --token "$GRAFANA_API_TOKEN" \
  --output-format json
```

相關指令：`change summary`、`change plan`、`status staged`。

## `assess-alerts`

用途：評估 alert 同步規格的 candidate、plan-only 與 blocked 狀態。

適用時機：當你想在 bundling 或 apply 前，先看 alert 資源會如何分類時。

主要旗標：`--alerts-file`、`--output-format`。

JSON shape：

- `kind`：`grafana-utils-alert-sync-plan`
- `schemaVersion`、`toolVersion`
- `summary`
  - `alertCount`、`candidateCount`、`planOnlyCount`、`blockedCount`
- `alerts`
  - `identity`、`title`、`managedFields`、`status`、`liveApplyAllowed`、`detail`

範例：

```bash
# 用途：assess-alerts。
grafana-util change assess-alerts --alerts-file ./alerts.json
```

```bash
# 用途：assess-alerts。
grafana-util change assess-alerts --alerts-file ./alerts.json --output-format json
```

相關指令：`change bundle`、`change bundle-preflight`、`overview`。

## `bundle`

用途：將匯出的 dashboards、alerting 資源、datasource inventory 與 metadata 打包成單一的本機 source bundle。

適用時機：當你想要一個統一的 bundle artifact，供後續同步、審核或 preflight 使用時。

主要旗標：`--dashboard-export-dir`、`--dashboard-provisioning-dir`、`--alert-export-dir`、`--datasource-export-file`、`--datasource-provisioning-file`、`--metadata-file`、`--output-file`、`--output-format`。

JSON shape：

- 這個指令有兩種輸出路徑
  - `--output-file`：把完整 source bundle contract 寫到檔案
  - `--output-format json`：把同一份 source bundle contract 印到 stdout
- source bundle 的 top-level 欄位：
  - `kind`、`schemaVersion`、`toolVersion`
  - `summary`
  - `dashboards`、`datasources`、`folders`、`alerts`
  - 可選 `alerting`
  - 可選 `metadata`

範例：

```bash
# 用途：bundle。
grafana-util change bundle --dashboard-export-dir ./dashboards/raw --alert-export-dir ./alerts/raw --output-file ./sync-source-bundle.json
```

```bash
# 用途：bundle。
grafana-util change bundle --dashboard-provisioning-dir ./dashboards/provisioning --alert-export-dir ./alerts/raw --output-file ./sync-source-bundle.json
```

相關指令：`change bundle-preflight`、`change promotion-preflight`、`snapshot export`。

## `bundle-preflight`

用途：根據 source bundle 與 target inventory 建立分階段的 bundle-level sync preflight 文件。

適用時機：當你需要在 apply 前比較 source bundle 與 target inventory 時。

主要旗標：`--source-bundle`、`--target-inventory`、`--availability-file`、`--fetch-live`、`--org-id`、`--output-format`。

JSON shape：

- `kind`：`grafana-utils-sync-bundle-preflight`
- `schemaVersion`
- `summary`
  - `resourceCount`
  - `syncBlockingCount`
  - `providerBlockingCount`
  - `secretPlaceholderBlockingCount`
  - `alertArtifactCount`
  - `alertArtifactBlockedCount`
  - `alertArtifactPlanOnlyCount`
- `syncPreflight`：巢狀 `grafana-utils-sync-preflight`
- `providerAssessment`：provider 摘要、plans 與 checks
- `secretPlaceholderAssessment`：placeholder 摘要、plans 與 checks
- `alertArtifactAssessment`：alert artifact 摘要與 checks

範例：

```bash
# 用途：bundle-preflight。
grafana-util change bundle-preflight --source-bundle ./sync-source-bundle.json --target-inventory ./target-inventory.json --output-format json
```

```bash
# 用途：bundle-preflight。
grafana-util change bundle-preflight --source-bundle ./sync-source-bundle.json --target-inventory ./target-inventory.json --availability-file ./availability.json --output-format json
```

相關指令：`change bundle`、`change promotion-preflight`、`status staged`。

## `promotion-preflight`

用途：根據 source bundle 與 target inventory 建立分階段的 promotion review handoff。

適用時機：當你準備進行 promotion review，並且需要明確的 mapping 與 availability 視圖時。

主要旗標：`--source-bundle`、`--target-inventory`、`--mapping-file`、`--availability-file`、`--fetch-live`、`--org-id`、`--output-format`。

JSON shape：

- `kind`：`grafana-utils-sync-promotion-preflight`
- `schemaVersion`、`toolVersion`
- `summary`
  - `resourceCount`、`directMatchCount`、`mappedCount`
  - `missingMappingCount`、`bundleBlockingCount`、`blockingCount`
- `bundlePreflight`：巢狀 bundle-preflight 結果
- `mappingSummary`
  - `mappingKind`、`mappingSchemaVersion`、`sourceEnvironment`、`targetEnvironment`
  - `folderMappingCount`、`datasourceUidMappingCount`、`datasourceNameMappingCount`
- `checkSummary`
  - `folderRemapCount`、`datasourceUidRemapCount`、`datasourceNameRemapCount`
  - `resolvedCount`、`directCount`、`mappedCount`、`missingTargetCount`
- `handoffSummary`
- `continuationSummary`
- `checks`、`resolvedChecks`、`blockingChecks`
  - 每筆包含 `kind`、`identity`、`sourceValue`、`targetValue`、`resolution`、`mappingSource`、`status`、`detail`、`blocking`

範例：

```bash
# 用途：promotion-preflight。
grafana-util change promotion-preflight --source-bundle ./sync-source-bundle.json --target-inventory ./target-inventory.json --mapping-file ./promotion-map.json --output-format json
```

```bash
# 用途：promotion-preflight。
grafana-util change promotion-preflight --source-bundle ./sync-source-bundle.json --target-inventory ./target-inventory.json --mapping-file ./promotion-map.json --availability-file ./availability.json --output-format json
```

相關指令：`change bundle-preflight`、`change apply`、`status live`。
