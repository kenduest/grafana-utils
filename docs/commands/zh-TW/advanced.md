# advanced

## 用途
`grafana-util advanced` 是給 expert/operator 用的 domain-specific 進階 namespace。

## 何時使用
當你已經知道自己要進哪個 subsystem，例如 dashboard import、alert authoring、datasource diff、access administration，就進這裡。

## 說明
`advanced` 保留了 `grafana-util` 原本完整的 domain 深度，但不再讓新手在第一眼就看到所有 lane。它是之後建議的 canonical expert 入口；舊的 top-level domain roots 仍然保留作為相容路徑。

## 子命令

- `advanced dashboard ...`
- `advanced alert ...`
- `advanced datasource ...`
- `advanced access ...`

## 範例
```bash
grafana-util advanced dashboard sync import --input-dir ./dashboards/raw --dry-run --table
```

```bash
grafana-util advanced alert author route preview --desired-dir ./alerts/desired --label team=sre --severity critical
```

```bash
grafana-util advanced datasource diff --diff-dir ./datasources --input-format inventory
```

```bash
grafana-util advanced access user diff --diff-dir ./access-users --scope global
```

## 相關指令

- [export](./export.md)
- [change](./change.md)
- [dashboard](./dashboard.md)
- [alert](./alert.md)
- [datasource](./datasource.md)
- [access](./access.md)
