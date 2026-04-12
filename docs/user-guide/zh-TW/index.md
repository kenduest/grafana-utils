# 維運導引手冊 (Operator Handbook)

## 語言切換

- 繁體中文手冊：[目前頁面](./index.md)
- English handbook: [英文手冊](../en/index.md)
- 繁體中文指令參考：[指令參考](../../commands/zh-TW/index.md)
- English command reference: [Command Reference](../../commands/en/index.md)

---

這份手冊是 `grafana-util` 的閱讀路線圖。先讀脈絡，再讀流程，最後才進到精確語法。如果你已經知道要找哪個 command family 或哪個 flag，就直接切到指令參考，不要讓手冊代替語法表。

## 如何閱讀這本手冊

1. 先看工具是拿來做什麼。
2. 再看開始使用章節。
3. 依照自己的角色或任務選章節。
4. 需要精確 subcommand 或 flags 時，切到指令參考。

## 書本結構

### 第 1 部：起步

- [這個工具是做什麼的](what-is-grafana-util.md)
- [開始使用](getting-started.md)

### 第 2 部：角色路徑

- [新手快速入門](role-new-user.md)
- [SRE / 維運角色導讀](role-sre-ops.md)
- [自動化 / CI 角色導讀](role-automation-ci.md)

### 第 3 部：操作面

- [Workspace 審查與狀態](status-workspace.md)
- [Dashboard 管理](dashboard.md)
- [Data source 管理](datasource.md)
- [告警治理](alert.md)
- [Access 管理](access.md)

### 第 4 部：設計原則

- [系統架構與設計原則](architecture.md)

### 第 5 部：參考與排錯

- [維運情境手冊](scenarios.md)
- [實戰錦囊與最佳實踐](recipes.md)
- [技術參考手冊](reference.md)
- [疑難排解與名詞解釋](troubleshooting.md)

## 依角色閱讀

- 新使用者：先看 [這個工具是做什麼的](what-is-grafana-util.md)，再看 [新手快速入門](role-new-user.md)，最後看 [開始使用](getting-started.md)。
- SRE / 維運人員：先看 [SRE / 維運角色導讀](role-sre-ops.md)，再看 [Workspace 審查與狀態](status-workspace.md)、[Dashboard 管理](dashboard.md)、[Data source 管理](datasource.md)、[疑難排解與名詞解釋](troubleshooting.md)。
- 身份 / 權限管理者：先看 [Access 管理](access.md)，再看 [技術參考手冊](reference.md)，最後切到 [指令參考](../../commands/zh-TW/index.md)。
- 自動化 / CI 維護者：先看 [自動化 / CI 角色導讀](role-automation-ci.md)，再看 [技術參考手冊](reference.md)，需要精確終端機語法時再看 [指令參考](../../commands/zh-TW/index.md)。
- 維護者 / 架構師：先看 [系統架構與設計原則](architecture.md)，再看 [開發者指南](../../DEVELOPER.md) 與 [docs/internal/README.md](../../internal/README.md)。

## 閱讀提示

- 頁尾的 `Next` 與 `Previous` 才是建議的連續閱讀方式。
- 手冊負責流程與脈絡，指令參考負責精確語法。
- 如果你要的是 terminal 風格的查找，直接開指令參考或 manpage，不要從記憶裡拼旗標。
