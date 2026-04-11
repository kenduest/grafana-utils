# `grafana-util observe`

## Root

用途：透過同一個 observe surface 做 live 與 staged 的 Grafana 唯讀檢查。

適用時機：當你想在 export、change review、或任何 domain-specific workflow 之前，先做安全的 read-only 檢查。

說明：`observe` 是公開的唯讀入口，負責 staged status、live status、project overview、snapshot，以及 generic resource read。把它當成預設的「先看再動手」入口；真的要進 mutation 或 domain-heavy workflow 時，再切去 `change` 或 `advanced`。

## 先從這裡開始

- `observe staged`：從本地 artifacts 顯示 staged readiness
- `observe live`：從 Grafana 顯示 live readiness
- `observe overview`：整理 staged 或 live 的整體摘要
- `observe snapshot`：建立或檢視本地 snapshot bundle
- `observe resource ...`：檢查 generic live resources

Examples:

```bash
# 用途：透過可重複使用的 repo-local profile 檢查 live readiness。
grafana-util observe live --profile prod --output-format yaml
```

```bash
# 用途：在 change preview 前先看 staged dashboard 與 alert artifacts。
grafana-util observe staged --dashboard-export-dir ./dashboards/raw --alert-export-dir ./alerts/raw --output-format text
```

```bash
# 用途：用較高層次的方式整理 staged workspace。
grafana-util observe overview --dashboard-export-dir ./dashboards/raw --alert-export-dir ./alerts/raw --output-format text
```

相關指令：`grafana-util change`、`grafana-util export`、`grafana-util config profile`。

## `staged`

用途：從 staged artifacts 產生 project status。

適用時機：當你要在 apply 前，用 machine-readable gate 檢查本地檔案是否準備好。

重要旗標：`--dashboard-export-dir`、`--dashboard-provisioning-dir`、`--datasource-export-dir`、`--datasource-provisioning-file`、`--access-user-export-dir`、`--access-team-export-dir`、`--access-org-export-dir`、`--access-service-account-export-dir`、`--desired-file`、`--source-bundle`、`--target-inventory`、`--alert-export-dir`、`--availability-file`、`--mapping-file`、`--output-format`。

Examples:

```bash
# 用途：從 raw dashboard artifacts 與 desired file 產生 staged status。
grafana-util observe staged --dashboard-export-dir ./dashboards/raw --desired-file ./desired.json --output-format table
```

```bash
# 用途：在 interactive workbench 裡檢查 staged status。
grafana-util observe staged --dashboard-provisioning-dir ./dashboards/provisioning --alert-export-dir ./alerts --output-format interactive
```

Machine-readable contract：`grafana-util-project-status`

## `live`

用途：從 live Grafana read surface 產生 project status。

適用時機：當你需要目前 Grafana 的 live 狀態，並可選擇疊上 staged sync context。

重要旗標：`--profile`、`--url`、`--token`、`--basic-user`、`--basic-password`、`--prompt-password`、`--prompt-token`、`--timeout`、`--verify-ssl`、`--insecure`、`--ca-cert`、`--all-orgs`、`--org-id`、`--sync-summary-file`、`--bundle-preflight-file`、`--promotion-summary-file`、`--mapping-file`、`--availability-file`、`--output-format`。

Examples:

```bash
# 用途：透過可重複使用的 profile 顯示 live status。
grafana-util observe live --profile prod --output-format yaml
```

```bash
# 用途：顯示帶 staged sync context 的 live status。
grafana-util observe live --url http://localhost:3000 --token "$GRAFANA_API_TOKEN" --sync-summary-file ./sync-summary.json --bundle-preflight-file ./bundle-preflight.json --output-format json
```

Machine-readable contract：`grafana-util-project-status`

## `overview`

用途：整理 project-wide staged 或 live context。

適用時機：當你想用一個較高層次的視角，同時看 dashboards、datasources、alerts、access 與 change artifacts。

重要旗標：像 `--dashboard-export-dir`、`--dashboard-provisioning-dir`、`--datasource-export-dir`、`--datasource-provisioning-file`、`--access-user-export-dir`、`--access-team-export-dir`、`--access-org-export-dir`、`--access-service-account-export-dir`、`--desired-file`、`--source-bundle`、`--target-inventory`、`--alert-export-dir`、`--availability-file`、`--mapping-file`、`--output-format` 這類 staged input 與 output flags。

Examples:

```bash
# 用途：整理 staged dashboard、alert 與 access artifacts。
grafana-util observe overview --dashboard-export-dir ./dashboards/raw --alert-export-dir ./alerts --desired-file ./desired.json --output-format table
```

```bash
# 用途：在 interactive workbench 顯示 live overview。
grafana-util observe overview live --url http://localhost:3000 --basic-user admin --basic-password admin --output-format interactive
```

相關指令：`grafana-util observe live`、`grafana-util change inspect`、`grafana-util snapshot review`。
