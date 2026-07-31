# Managed blocks 與備份

## 指令區塊

只維護：

```markdown
<!-- AIOS:START -->
AIOS root: <absolute-local-path>
Edition: company | personal
Managed by: sync-aios-global

<tool-specific instructions>
<!-- AIOS:END -->
```

規則：

- 區塊外逐 byte 保留。
- 沒有區塊時加在檔案末尾。
- 已有一組完整區塊時只替換區塊內文。
- 有多組、缺少 end marker、順序錯誤或巢狀時停止。
- managed block 不放 token、私人記憶正文或未授權公司內容。

## Claude Code 區塊

使用目前 Claude Code 支援的 import／memory 語法指向 AIOS 的 `CLAUDE.md`。寫入後開新 session，要求工具回報載入的 AIOS edition 以驗證。

## Codex 區塊

Codex 的全域 `AGENTS.md` 由 `${CODEX_HOME:-~/.codex}` 讀取；不要使用 Claude `@import` 語法冒充 Codex 匯入。

managed block 應包含：

- AIOS 根路徑與 edition。
- 簡短工作原則。
- 從 AIOS 或其專案資料夾工作時，以 repo `AGENTS.md` 為較具體規則。
- 必要時由 sync skill 重新產生區塊，而不是承諾 Codex會自動讀另一個任意 Markdown。

## 備份

位置：

```text
private/backups/global-sync/<YYYYMMDD-HHMMSS>/
├── manifest.md
├── claude/
└── codex/
```

`manifest.md` 記錄：

- OS
- 來源與目標路徑
- 檔案 hash
- link 類型與 link target
- 預計動作

不要備份：

- auth、credentials、session
- `.env`
- MCP OAuth 資料
- cache、logs、output

## 同名 Skill

同名比較至少包含：

- frontmatter `name`
- description
- 檔案清單
- `SKILL.md` hash
- 是否含絕對路徑
- license／來源檔是否存在

預設保留使用者既有版本。只有使用者明確選擇後，才更新、改名或把另一版放入 AIOS。
