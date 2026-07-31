# 版本紀錄（Changelog）

格式依 [Keep a Changelog](https://keepachangelog.com/zh-TW/)；安裝版本以 `.aios/version.md` 為準。

## [0.2.3] - 2026-08-01

### 新增

- **財務分析技能 21 件**：自 Anthropic 官方 financial-services plugin（Apache-2.0）抽出、去重，
  轉為工具中立的資料夾技能，Claude Code 與 Codex 皆可使用。涵蓋估值建模（DCF／LBO／三表／comps）、
  試算表稽核與清理、投行級簡報 QC、研究報告與日常追蹤。LICENSE 存於 `docs/licenses/`。
- plugin 內的 `skill-creator` 與既有同名技能衝突，未收錄。

### 移除

- `.claude/settings.json` 的 plugin 綁定：改由資料夾技能提供相同能力，
  不再強制 Claude Code 使用者自動安裝 marketplace plugin，也讓 Codex 使用者取得同等功能。

## [0.2.2] - 2026-08-01

### 新增

- `docs/`：功能總覽（FEATURES.md）與本版本紀錄。
- FEATURES.md 補記官方 financial-services plugin 清單（該節於 0.2.3 改寫為雙工具共用技能）。

## [0.2.1] - 2026-07-31

### 新增

- **技能擴充（12 → 38）**：
  - `install-aios`：新電腦一鍵安裝——抓取範本、補私人層、訪談、全域整合，完成後接續詢問 Set up。（`d16e30f`、`bcbdc08`）
  - `hyperframes` 影片套件完整版：入口＋6 領域技能＋9 工作流＋3 輔助（Apache-2.0，含 LICENSE）。clone 後即可出片，不需另外 `npx skills add`。（`e1e33b3`、`d0d7751`）
  - `video-spec-builder`：分鏡訪談，產出 video-spec.md 交 HyperFrames 渲染（MIT）。（`e1e33b3`）
  - `cards`：IG／Threads／X 輪播圖卡（ISC；不含 node_modules，首次使用 `npm install`）。（`96d6c75`）
  - `grilling`＋`grill-me`：計畫烤問模式。（`96d6c75`）
  - `meeting-notes-reference`：會議記錄結構化＋Breeze-ASR-25 本機轉錄三段式管線（ffmpeg 前處理 → CPU int8 推論 → 術語校正）。術語表為空白範本。（`63942b2`）
- `setup-aios` 加入技能庫，可在此 AIOS 內直接建立新的 AIOS。

## [0.2.0] - 2026-07-31

### 新增

- 初始公開發布（`4a7caf7`）：
  - 共用骨架：雙工具入口（`CLAUDE.md`／`AGENTS.md`）、`.aios/` 設定、`.gitignore`。
  - 個人 Context 與記憶系統範本（`private/`，不進 Git，由 materializer 於本機生成）。
  - `knowledge/` Obsidian 相容知識庫。
  - 預設技能 12 件：brainstorm、docx、pdf、pptx、xlsx、markitdown、obsidian-vault、review-memory、skill-creator、speak-human-tw、sync-aios-global、update-wiki。
