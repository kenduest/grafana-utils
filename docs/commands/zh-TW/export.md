# export

## 用途
`grafana-util export` 是給常見備份與本地 inventory 擷取工作的 task-first 入口。

## 何時使用
當你的工作就是單純匯出或備份，而不想一開始就進入 domain-heavy 的進階樹時，請先用這個 namespace。

## 說明
`export` 故意保持狹窄。它只是包住既有的 domain export 流程，不改變底層行為，讓第一次使用的人不用先理解整棵 `dashboard`、`alert`、`datasource`、`access` 命令樹。

## 子命令

- `export dashboard`
- `export alert`
- `export datasource`
- `export access user`
- `export access org`
- `export access team`
- `export access service-account`

## 範例
```bash
grafana-util export dashboard --output-dir ./dashboards --overwrite
```

```bash
grafana-util export alert --output-dir ./alerts --overwrite
```

```bash
grafana-util export datasource --output-dir ./datasources
```

```bash
grafana-util export access service-account --output-dir ./access-service-accounts
```

## 相關指令

- [advanced](./advanced.md)
- [dashboard export](./dashboard-export.md)
- [alert export](./alert-export.md)
- [datasource export](./datasource-export.md)
- [access](./access.md)
