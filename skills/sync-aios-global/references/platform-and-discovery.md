# 平台與探索位置

不要只靠路徑存在就認定工具會讀取；先檢查目前安裝、環境變數與官方探索規則。

## 共同原則

- Home 由環境與 OS API 解析，不寫死使用者名稱。
- AIOS 內一律保存相對路徑；絕對路徑只出現在 ignored 的本機設定或 global managed block。
- 連結建立前辨識實體資料夾、Symlink、Windows Junction 與失效連結。
- 不以掃描整顆磁碟尋找設定。

## Claude Code

常見使用者位置：

```text
~/.claude/CLAUDE.md
~/.claude/skills/
```

實際修改前檢查目前 Claude Code 安裝與既有設定。保留應用程式專屬 MCP、plugin、auth 與 session。

## Codex

Codex home 預設是 `~/.codex`，但 `CODEX_HOME` 可覆蓋。

全域指令：

```text
${CODEX_HOME:-~/.codex}/AGENTS.md
```

若存在非空 `AGENTS.override.md`，Codex 會優先讀它；必須回報這件事，不把 managed block 寫進未生效的 `AGENTS.md` 後假稱已完成。

官方使用者 Skills 位置：

```text
~/.agents/skills/
```

Codex 支援被 Symlink 的 Skill 資料夾。若環境中另有 `~/.codex/skills/` 等既有位置，把它列入盤點，但先驗證目前版本是否實際使用；不要只因舊設定存在就把它當唯一入口。

## 連結策略

### Windows

- 目錄 Junction 不要求 Developer Mode，適合本機同磁碟目錄。
- Symlink 可跨更多情境，但可能需要權限或 Developer Mode。
- 不可對現有非空實體資料夾直接建立 Junction。

### macOS／Linux

- 使用相對 Symlink，方便 AIOS 根目錄搬移。
- 建立前使用 `readlink` 或等價方式確認既有目標。

### 降級

無法建立連結時：

1. 保留原資料夾。
2. 詢問是否 copy-mode。
3. 只複製使用者確認的 Skills。
4. 在 `.aios/manifest.md` 記錄來源、時間與需手動重同步。
