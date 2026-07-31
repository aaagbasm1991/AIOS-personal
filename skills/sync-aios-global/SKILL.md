---
name: sync-aios-global
description: 安全盤點並整合目前 AIOS 與使用者既有的 Claude Code、Codex 全域指令和 Skills，支援 Windows、macOS、Linux、實體資料夾、Symlink 與 Junction；採備份、受控區塊及同名保留策略。當使用者提到同步 AIOS 到全域、讓 Claude 與 Codex 共用資料夾／Skills、設定全域 CLAUDE.md／AGENTS.md、整合既有全域設定或換機初始化時使用。
---

# Sync AIOS Global

把同一套 AIOS 安全接入 Claude Code 與 Codex，但不覆蓋使用者已建立的規則、Skills、記憶或本機資料。

## 必讀

- 盤點 OS、路徑與工具探索位置前，讀 [platform-and-discovery.md](references/platform-and-discovery.md)。
- 準備修改任何全域檔案前，讀 [managed-blocks-and-backups.md](references/managed-blocks-and-backups.md)。

## 預設行為

只盤點並提出方案。修改全域檔案、建立連結、複製 Skill 或安裝軟體前，都要取得使用者明確同意。

不得同步：

- token、credential、`.env`
- OAuth、session、登入資料
- MCP 私密設定
- plugin cache、模型 cache、執行輸出
- 私人記憶、journal、未授權公司資料

## 工作流程

### 1. 驗證 AIOS 根目錄

根目錄必須包含：

- `.aios/`
- `skills/`
- `CLAUDE.md`
- `AGENTS.md`

讀 `.aios/edition.md` 與 manifest，確認是使用者指定的 personal 或 company AIOS。不要依資料夾名稱猜情境。

### 2. 盤點既有設定

唯讀檢查：

- Claude Code 全域指令與 Skills。
- Codex home、全域 `AGENTS.md`、官方使用者 Skills 位置，以及現存的 legacy Skills 位置。
- 每個 Skills 目標是實體資料夾、Symlink、Junction 或失效連結。
- 既有 managed block、備份與同名 Skill。

不要打開 credential、auth、session、`.env` 或 cache 正文。

### 3. 顯示整合報告

把現有自訂 Skills 分成：

- 可共用候選
- 私人或本機專用
- 含硬編碼路徑
- 同名衝突
- 授權待確認

預設只顯示報告，不自動複製進 AIOS。只有使用者確認的團隊共用 Skill 才可進 `skills/` 和 Git。

### 4. 備份

每次寫入前：

1. 建立 timestamped 備份到 `<aios-root>/private/backups/global-sync/`。
2. 保存目標檔案及連結資訊，但不複製秘密或大型 cache。
3. 顯示備份位置。
4. 備份失敗就停止，不繼續修改。

### 5. 合併全域指令

- 保留既有全域 `CLAUDE.md`、`AGENTS.md` 的受控區塊外內容。
- 只建立或更新 `AIOS:START`／`AIOS:END` 區塊。
- Claude Code 使用其支援的 project memory／import 方式連到 AIOS `CLAUDE.md`。
- Codex 不假裝支援 Claude 的 `@import`；將精簡且可驗證的 AIOS 全域基底同步進 managed block，並保留來源路徑。
- Codex 專案情境仍由 repo 內較接近工作目錄的 `AGENTS.md` 自動套用。
- 檔案已有不完整、重複或交錯 managed block 時停止，先讓使用者判斷。

### 6. 整合 Skills

`<aios-root>/skills/` 是共同來源。

- 專案層：把 `<aios-root>/.agents/skills` 與 `<aios-root>/.claude/skills` 連至共同來源。
- 全域層：優先逐一連結缺少的 Skill，保留原有 Skills 資料夾。
- 同名時保留使用者既有版本；比較 metadata 與檔案差異，交由使用者決定。
- 既有連結已指向正確 AIOS 時跳過。
- 既有連結指向其他位置時顯示來源與影響，不直接替換。
- 無法建立連結時才採 copy-mode，並在 manifest 記錄同步責任。

私人 Skill 可留在既有全域位置，或存放於 AIOS 的 `private/skills/` 後逐一連結；不得加入團隊 Git。

### 7. 驗證

逐項確認：

- 全域指令檔只有 managed block 被改動。
- 備份可讀。
- Claude Code 與 Codex 各自能看到預期入口。
- 每個已接入 Skill 都有 `SKILL.md`。
- 同名 Skill 沒有被覆蓋。
- 沒有 AIOS 外私人路徑被寫入 tracked 檔案。
- 沒有秘密、cache 或個人記憶被同步。

若 Codex 指令剛更新，提醒新 session 才會重新載入 instruction chain。

## 完成回報

列出：

- OS 與 AIOS 根目錄。
- 掃描過的設定位置。
- 備份位置。
- 實際更新的 managed blocks。
- link／copy-mode 的 Skills。
- 保留的同名或私人 Skills。
- 需要重新啟動或開新 session 的工具。

只回報已驗證成功的項目。
