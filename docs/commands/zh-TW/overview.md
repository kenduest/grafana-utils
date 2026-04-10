# 已移除的 root path：`grafana-util overview`

## Root

用途：已移除 project-wide overview root 的遷移說明。

適用時機：當你在對照舊文件或舊腳本，想對應到目前的 `observe` surface 時。

說明：目前公開的 overview surface 已移到 `grafana-util observe`。top-level `overview` root 已不可直接執行。請改用 `observe overview` 或 `observe live`。

Canonical replacement：

- `grafana-util overview ...` -> `grafana-util observe overview ...`
- `grafana-util overview live ...` -> `grafana-util observe overview live ...`

下一步請看：[observe](./observe.md)
