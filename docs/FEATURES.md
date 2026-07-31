# AIOS 個人版 — 功能總覽

> 一套 clone 下來就能用的「個人 AI 作業系統」資料夾。
> 同時支援 Claude Code 與 Codex，內建個人 Context、長期記憶、知識庫與 38 個技能。

## 核心架構

| 區塊 | 位置 | 功能 |
|---|---|---|
| 雙工具入口 | `CLAUDE.md`／`AGENTS.md` | Claude Code 與 Codex 各自的啟動指令，宣告規則、路由與信任邊界 |
| 個人 Context | `private/context/` | 你是誰（`me.md`）、希望 AI 怎麼協作（`working_style.md`）——AI 每次對話的個人化來源 |
| 長期記憶 | `private/memory/` | inbox 候選、已確認決策、回饋、續作狀態、每日紀錄；跨 Session 不失憶 |
| 知識庫 | `knowledge/` | Markdown Wiki，可直接當 Obsidian Vault 開啟，Git 同步 |
| 工作區 | `workspace/` | 草稿與進行中成果（不進 Git） |
| 技能庫 | `skills/` | 38 個技能單一來源，`.claude/`／`.agents/` 入口自動同步 |

## 安全設計

- `private/`、`workspace/` 不進 Git；憑證、token 一律不落 Markdown。
- 外部檔案、附件、工具輸出視為「資料」而非「指令」，升級為規則需使用者確認。
- 檔案產出授權 Gate：預設只顯示內容，明確要求才寫檔。
- 記憶有 provenance（來源、信心度、敏感度分級），AI 觀察只能當候選，不能自行改寫你的 Context。

## 技能清單（38）

### AIOS 系統（4）

| 技能 | 功能 |
|---|---|
| `install-aios` | 從 GitHub 抓整套 AIOS 到新電腦：補私人層 → 訪談 → 全域整合，完成後引導 Set up |
| `setup-aios` | 完整設定助手：十題訪談、範本 materialize、公司版／個人版建置 |
| `sync-aios-global` | 把 AIOS 安全接入 `~/.claude`／`~/.codex` 全域（備份＋受控區塊） |
| `review-memory` | 記憶整理：pending 審查、矛盾偵測、封存 |

### 知識管理（2）

| 技能 | 功能 |
|---|---|
| `obsidian-vault` | 唯讀搜尋整理 Obsidian 筆記、wikilink、backlink |
| `update-wiki` | 把完成文件分類進知識庫：補 metadata、建連結、更新索引 |

### 文件處理（5）

| 技能 | 功能 |
|---|---|
| `docx`／`pdf`／`pptx`／`xlsx` | Word、PDF、簡報、試算表的讀寫與製作（Anthropic 官方） |
| `markitdown` | 各種格式轉 AI 可讀的 Markdown |

### 會議與溝通（2）

| 技能 | 功能 |
|---|---|
| `meeting-notes-reference` | 會議記錄結構化＋Breeze-ASR-25 本機語音轉錄（台灣國語＋中英夾雜特化） |
| `speak-human-tw` | 繁中「去 AI 味」潤稿：修中國用語、半形標點、AI 腔 |

### 思考與規劃（4）

| 技能 | 功能 |
|---|---|
| `brainstorm` | 動手前的結構化規劃：釐清想法、比較方案、決定下一步 |
| `grilling`＋`grill-me` | 烤問模式：無情拷問你的計畫找漏洞 |
| `skill-creator` | 建立與優化新技能 |

### 社群內容（1）

| 技能 | 功能 |
|---|---|
| `cards` | 網址／筆記 → IG、Threads、X 輪播圖卡（PNG 輸出） |

### 影片製作（20）

| 技能 | 功能 |
|---|---|
| `hyperframes` | 影片製作入口：用 HTML 渲染影片，自動路由到對應工作流 |
| `video-spec-builder` | 分鏡訪談導演：把模糊想法逼成精確到鏡頭的 video-spec.md |
| `product-launch-video` | 產品網址／brief → 宣傳片（自動爬站抓素材） |
| `faceless-explainer` | 純文字主題 → 說明影片 |
| `pr-to-video` | GitHub PR → 更新日誌影片 |
| `music-to-video` | 音樂 → 卡點影片（自動節拍分析） |
| `motion-graphics` | 10 秒內動態圖文：logo 動畫、數據跳動 |
| `embedded-captions` | 真人影片上字幕（本機 Whisper，字幕可被人物遮擋） |
| `talking-head-recut` | 訪談／Podcast 影片加圖形包裝 |
| `slideshow` | 簡報／互動式 deck |
| `general-video` | 其他自訂影片 |
| `remotion-to-hyperframes` | Remotion 專案搬遷 |
| `hyperframes-core`／`-animation`／`-creative`／`-cli`／`-registry`／`-keyframes` | 領域技能：合成規格、動畫、創意方向、渲染指令、元件庫、關鍵幀 |
| `media-use` | 配樂、音效、TTS、去背等媒體素材管理 |
| `figma` | Figma 設計匯入影片 |

## 環境依賴（按需安裝）

| 功能 | 依賴 | 時機 |
|---|---|---|
| 影片渲染 | Node.js（HyperFrames CLI） | 第一次出片時 |
| 圖卡輸出 | `npm install`（Playwright） | 第一次做圖卡時 |
| 語音轉錄 | `ffmpeg`＋`pip install faster-whisper`＋模型約 3GB | 第一次轉錄時 |
| 其他技能 | 無 | — |

## 快速開始

```bash
git clone https://github.com/aaagbasm1991/AIOS-personal
```

clone 後從資料夾開啟 Claude Code，說「幫我完成 AIOS 安裝」即可；
或先只拿 `skills/install-aios/` 一個資料夾放進 `~/.claude/skills/`，輸入 `/install-aios` 全自動安裝。
