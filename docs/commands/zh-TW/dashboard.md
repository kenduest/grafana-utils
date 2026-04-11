# dashboard

## 指令分類

- 瀏覽與檢視：先找 dashboard、讀內容、看變數或歷史版本。常用子命令：`browse`、`list`、`get`、`variables`、`history`。
- 匯出與匯入：在 Grafana、raw JSON、prompt JSON、provisioning 檔案之間搬移 dashboard。常用子命令：`export`、`import`、`convert raw-to-prompt`。
- 審查與比對：做差異比對、草稿檢查、相依性分析、影響面或治理檢查。常用子命令：`diff`、`review`、`summary`、`dependencies`、`impact`、`policy`。
- 編修與發佈：建立或修改本地草稿，再有意識地發佈或刪除。常用子命令：`get`、`clone`、`patch`、`serve`、`edit-live`、`publish`、`delete`。
- 操作與截圖：為報告、事故或交接取得視覺證據。常用子命令：`screenshot`。

指令路徑仍維持扁平，例如 `grafana-util dashboard list`。分類只用在 help 與文件導覽，避免再加一層不必要的 namespace。

## 從這裡開始

- 先看現況：`dashboard browse` 或 `dashboard list`
- 先做草稿：`dashboard get`、`dashboard clone`、`dashboard export`
- 先做比對：`dashboard diff`、`dashboard review`
- 先做分析：`dashboard summary --input-dir ...`、`dashboard summary --url ...`、`dashboard variables`
- 先做上線前檢查：`dashboard policy`
- 先看相依性與影響面：`dashboard dependencies`、`dashboard impact`
- 先處理歷史版本：`dashboard history list`、`dashboard history restore`、`dashboard history export`
- 先拿素材：`dashboard screenshot`

## 說明

`grafana-util dashboard` 把 dashboard 相關工作收在同一個入口：從瀏覽、草稿、匯出、匯入、比對，到相依性、影響面、政策和截圖。它也可用 `grafana-util db` 呼叫。命令本身維持扁平，help 和文件用分組降低閱讀壓力。

新的 canonical 路徑是：
- `dashboard browse`
- `dashboard list`
- `dashboard variables`
- `dashboard get`
- `dashboard clone`
- `dashboard edit-live`
- `dashboard review`
- `dashboard patch`
- `dashboard serve`
- `dashboard publish`
- `dashboard export`
- `dashboard import`
- `dashboard diff`
- `dashboard convert raw-to-prompt`
- `dashboard summary`
- `dashboard dependencies`
- `dashboard policy`
- `dashboard screenshot`

如果是單一 dashboard 的 authoring 路徑，建議把它想成：
- `dashboard get` 或 `dashboard clone`：先做草稿
- `dashboard serve`：用本地 preview server 持續檢視草稿內容，必要時也能自動打開瀏覽器
- `dashboard review`：先驗證草稿內容
- `dashboard patch`：改寫本地中繼資料
- `dashboard edit-live`：從 live 拉一份進 editor，預設仍先落回本地草稿，而且會依 review 結果決定能不能回寫 live
- `dashboard publish`：沿用 import pipeline 發回 Grafana

`review`、`patch`、`publish` 也都支援 `--input -`，可以直接吃標準輸入的一份 wrapped 或 bare dashboard JSON。這適合外部 generator 已經把 JSON 寫到 stdout 的情況。`patch --input -` 必須搭配 `--output`，若你是在本地反覆編修同一份檔案，則改用 `publish --watch`；它只支援本地檔案路徑，不支援 `--input -`。

## 歷史與還原工作流

如果你的問題不是「現在這份 dashboard 長什麼樣」，而是「哪個舊版本應該被救回來並變成新的最新版本」，就看這一組。

- [dashboard history](./dashboard-history.md)
- `dashboard history list`：列出單一 dashboard UID 的最近版本歷史。
- `dashboard history restore`：把某個歷史版本複製成新的最新 Grafana 版本。
- `dashboard history export`：把歷史版本匯出成可重用的 JSON 成品，方便審查或 CI。

這條路徑最適合要找回已知可用版本，但不想手動重建 dashboard 的情況。

## 採用前後對照

- **採用前**：dashboard 動作常分散在 UI、草稿 JSON 與臨時 shell 指令裡，要回頭重跑很麻煩。
- **採用後**：同一條命令群組就能把瀏覽、草稿、檢查、發佈與素材產生串起來。

## 成功判準

- 你能在開始前就判斷這次是要看 live、做草稿、跑檢查，還是直接發佈
- export / summary / diff 的產物能互相對得起來，不會換個步驟就失去上下文
- 需要交給 review 或 CI 時，可以把 dependencies / impact / policy 的結果拿去重跑

## 失敗時先檢查

- 如果 browse 或 inspect 結果比預期少，先核對 `--profile`、`--url`、org 與權限
- 如果 dependencies 或 impact 是空的，先確認你餵的是同一次 inspect 產物
- 如果政策檢查看起來怪怪的，先看 `governance` 和 `queries` 是否來自相同來源

## 重點旗標

- `--url`：Grafana 基底網址。
- `--token`、`--basic-user`、`--basic-password`：共用的線上 Grafana 憑證。
- `--profile`：從 `grafana-util.yaml` 載入 repo 本地預設值。
- `--color`：控制這個指令群組的 JSON 彩色輸出。

## 範例

```bash
# 先看 dashboard 長什麼樣，再決定下一步要走哪條工作流。
grafana-util dashboard browse --profile prod
```

```bash
# 先盤點現況，再決定要走 browse 或 export。
grafana-util dashboard list --profile prod
```

```bash
# 先做 live 分析，再決定要不要匯出或截圖。
grafana-util dashboard summary --url http://localhost:3000 --basic-user admin --basic-password admin --interactive
```

```bash
# 先產生治理輸出，留給 dependencies 或 policy 接著用。
grafana-util dashboard summary --url http://localhost:3000 --token "$GRAFANA_API_TOKEN" --output-format governance
```

```bash
# 先從標準輸入 review 一份生成儀表板，再決定要不要 publish。
jsonnet dashboards/cpu.jsonnet | grafana-util dashboard review --input - --output-format json
```

```bash
# 編修本地草稿時，每次儲存後自動重跑 publish dry-run。
grafana-util dashboard publish --url http://localhost:3000 --basic-user admin --basic-password admin --input ./drafts/cpu-main.json --dry-run --watch
```

```bash
# 開一個本地 preview server，持續檢視單一 dashboard 草稿。
grafana-util dashboard serve --input ./drafts/cpu-main.json --port 18080 --open-browser
```

```bash
# 從 live dashboard 開始編修，但預設先輸出成新的本地草稿。
grafana-util dashboard edit-live --profile prod --dashboard-uid cpu-main --output ./drafts/cpu-main.edited.json
```

## 相關指令

### 瀏覽與檢視

- [dashboard browse](./dashboard-browse.md)
- [dashboard list](./dashboard-list.md)
- [dashboard get](./dashboard-get.md)
- [dashboard variables](./dashboard-variables.md)
- [dashboard history](./dashboard-history.md)

### 匯出與匯入

- [dashboard export](./dashboard-export.md)
- [dashboard import](./dashboard-import.md)
- [dashboard convert raw-to-prompt](./dashboard-convert-raw-to-prompt.md)

### 審查與比對

- [dashboard diff](./dashboard-diff.md)
- [dashboard review](./dashboard-review.md)
- [dashboard summary](./dashboard-summary.md)
- [dashboard dependencies](./dashboard-dependencies.md)
- [dashboard impact](./dashboard-impact.md)
- [dashboard policy](./dashboard-policy.md)

### 編修與發佈

- [dashboard get](./dashboard-get.md)
- [dashboard clone](./dashboard-clone.md)
- [dashboard patch](./dashboard-patch.md)
- [dashboard serve](./dashboard-serve.md)
- [dashboard edit-live](./dashboard-edit-live.md)
- [dashboard publish](./dashboard-publish.md)
- [dashboard delete](./dashboard-delete.md)

### 操作與截圖

- [dashboard screenshot](./dashboard-screenshot.md)
