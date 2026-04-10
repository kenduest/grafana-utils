# 已移除的 root path：`grafana-util status`

## Root

用途：已移除 staged/live status root 的遷移說明。

適用時機：當你在對照舊文件或舊腳本，想對應到目前的 `observe` surface 時。

說明：目前公開的 staged/live status surface 已移到 `grafana-util observe`。top-level `status` root 已不可直接執行。請改用 `observe staged`、`observe live`、`observe overview` 或 `observe snapshot`。

Canonical replacement：

- `grafana-util status staged ...` -> `grafana-util observe staged ...`
- `grafana-util status live ...` -> `grafana-util observe live ...`

下一步請看：[observe](./observe.md)
