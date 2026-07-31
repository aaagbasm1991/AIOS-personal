---
name: aios-doctor
description: >
  AIOS 健檢：檢查雙入口（CLAUDE.md／AGENTS.md）規則是否漂移、三處 Skills
  是否一致、記憶系統與 MCP 狀態，並引導 fresh-session 載入驗證。只盤點與
  提出建議，不修改任何檔案。當使用者提到 AIOS 健檢、檢查 AIOS、aios-doctor、
  規則有沒有不一致、Claude 和 Codex 有沒有對齊、技能有沒有壞掉時使用。
---

# AIOS Doctor — 健檢助手

對目前的 AIOS 安裝做全面唯讀健檢。**本 Skill 不修改任何檔案**——發現問題
只列入報告，由使用者決定是否修復（修復可交給 `setup-aios` 或人工處理）。

## 原則

1. 全程唯讀；任何修復動作都先徵求同意再另行執行。
2. 報告只列名稱與狀態，**不得**貼出設定檔全文——`settings.json`、
   `config.toml`、`.mcp.json` 可能含 token、路徑或私密資訊。
3. 不開啟 `private/memory/` 正文，只檢查檔案存在與筆數。
4. 結論先行：報告開頭先給「健康／需注意／有問題」總評。

## 檢查步驟

### 1. 安裝位置與版本

- 確認目前資料夾含 `.aios/`、`skills/`、`CLAUDE.md`、`AGENTS.md`（缺任一即非完整 AIOS，停止並回報）。
- 讀 `.aios/edition.md`、`version.md`、`manifest.md`：edition／version 三處是否一致。
- `git remote -v` 看有無 remote；有 GitHub remote 時用 `gh repo view --json visibility`
  確認 public／private（查不到就標「待確認」，不要猜）。
- public repo 時抽查 `git ls-files` 沒有 `private/`、`workspace/` 的檔案。

### 2. 雙入口規則漂移

`CLAUDE.md` 與 `AGENTS.md` 是**平行維護**的兩份檔案，最常見的退化就是
只改了一邊。逐項比對：

- 兩檔都存在且非空。
- 抽出兩檔的 `## ` 章節標題清單並排比對：只存在於單邊的章節，逐一判斷是
  「平台專屬（合理）」還是「漏同步（漂移）」。平台專屬章節例：Claude 的
  plugin 設定說明、Codex 的 Karpathy 索引。
- 對共同章節（身份、協作方式、信任邊界、記憶路由、安全規則），比對語意是否
  一致——不要求逐字相同，但規則的實質內容（gate 條件、路由目的地、優先順序）
  不能矛盾。發現矛盾時引用兩邊的原句讓使用者裁決。
- 全域層：`~/.claude/CLAUDE.md` 與 Codex 全域 `AGENTS.md` 是否存在且非空
  （空檔不算錯誤，但要提醒全域偏好不會自己長出來）。

### 3. Skills 三處一致性

copy 模式（看 `manifest.md` 的 `skills_mode`）用簽章驗證：

```bash
PYTHONDONTWRITEBYTECODE=1 python -c "
import sys
sys.path.insert(0, 'skills/setup-aios/scripts')
from materialize import tree_signature
from pathlib import Path
sigs = {p: tree_signature(Path(p)) for p in ('skills', '.agents/skills', '.claude/skills')}
for k, v in sigs.items(): print(k, v[:16])
print('all match:', len(set(sigs.values())) == 1)
print('manifest match:', list(sigs.values())[0][:16] in Path('.aios/manifest.md').read_text(encoding='utf-8'))
"
```

- 三處簽章一致＋與 manifest 相符 → 健康。
- 入口簽章與 manifest 記錄的舊簽章一致、僅根 `skills/` 較新 → 待同步
  （重跑 materializer 即可，屬低風險）。
- 入口簽章三者皆不同 → 有人工修改過入口副本，列為需人工裁決，**不可自動覆蓋**。
- link 模式則驗證兩個入口實際解析到 `<aios-root>/skills`，並列出失效連結。
- 每個技能資料夾都含 `SKILL.md`；缺少者列出。
- 與全域技能（`~/.claude/skills`、`~/.agents/skills`）比對同名：同名不是錯誤，
  但要列出讓使用者知道實際會載入哪一份。

### 4. MCP 與 plugin（僅列名稱）

- Claude Code：`claude mcp list` 可用就用；否則檢查 `.mcp.json`／專案設定，
  只列 server 名稱。`.claude/settings.json` 有 enabledPlugins 時列出 plugin 名稱。
- Codex：`codex mcp list` 可用就用；否則看 `~/.codex/config.toml` 的
  `[mcp_servers.*]` 段名。
- 兩邊清單並排：哪些只有單邊有。提醒：MCP 設定不跨工具共用是 AIOS 的設計，
  單邊有不算錯誤；但使用者以為兩邊都有的要標出來。

### 5. 記憶系統

只檢查結構，不讀正文：

- `private/context/me.md`、`working_style.md` 存在且非範本空殼（有無殘留占位符）。
- `private/memory/` 的 index、inbox、active-context、review-state、daily/ 存在。
- inbox pending 筆數、review-state 距上次整理天數——超過 `review-memory`
  的觸發條件（pending ≥ 10 或 > 7 天）時建議整理。
- `.gitignore` 確實排除 `private/`、`workspace/`、`.aios/local.md`。

### 6. Fresh-session 載入驗證（檔案存在 ≠ 真的有載入）

這步無法全自動，給使用者明確指引：

> 分別開一個**全新的** Claude Code 與 Codex 對話（在 AIOS 根目錄），問它：
> 「這次對話你載入了哪些規則來源？列出檔案路徑與先後順序。」
>
> 預期：全域規則先載入，AIOS 根入口後載入；兩者衝突時 AI 應說明以較接近
> 工作目錄的規則為準。若某一邊完全沒提到 AIOS 根入口，代表該工具沒讀到
> ——常見原因：不是從 AIOS 根目錄開啟、入口檔名錯誤、或全域設定攔截。

### 7. 輸出報告

```markdown
# AIOS 健檢報告

**總評**：健康／需注意／有問題

## 現況
- 位置與版本：
- 雙入口：一致／發現 N 處漂移
- Skills：三處一致／待同步／需人工裁決
- MCP／plugin：Claude N 個、Codex N 個
- 記憶：正常／inbox 待整理 N 筆

## 發現的問題（依嚴重度排序）
1. …（每項附：影響、建議修法、是否可自動修復）

## 建議下一步
- …（需要使用者確認的事項單獨列出）
```

報告後停止。使用者同意修復時，優先交給 `setup-aios`（升級／重跑 materializer）
或 `sync-aios-global`（全域整合），不要在本 Skill 內直接改檔。
