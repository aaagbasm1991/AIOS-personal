# AIOS — 功能總覽

把這個資料夾 clone 下來，從資料夾開啟 Claude Code 或 Codex，就得到一個
「記得你是誰、內建 59 個技能」的個人 AI 工作環境。

它與直接使用 AI 工具的差別：

- **有記憶**：你是誰、偏好怎麼協作、專案做到哪，寫在 `private/`（只存本機，不進 Git）。
- **技能開箱即用**：不用自己找 prompt 或裝擴充，說一句話就觸發對應流程。

各功能附「可以這樣說」的例句，照著講即可觸發。

## 安裝與系統

| 技能 | 功能 | 可以這樣說 |
|---|---|---|
| `install-aios` | 在新電腦自動下載整套、建立私人層、訪談建立個人 Context、詢問是否接入全域 | 「幫我從 GitHub 安裝 AIOS」 |
| `setup-aios` | 完整設定助手：訪談、範本生成、升級 | 「幫我升級 AIOS」 |
| `sync-aios-global` | 把 AIOS 安全接入 `~/.claude`／`~/.codex` 全域（先備份） | 「把 AIOS 同步到全域」 |

## 開會與文件

| 技能 | 功能 | 可以這樣說 |
|---|---|---|
| `meeting-notes-reference` | 會議錄音在本機轉逐字稿（Breeze-ASR-25，台灣國語＋中英夾雜特化，不上傳雲端），依術語表校正後整理成含決議、負責人、期限的記錄 | 「幫我把這個錄音整理成會議記錄」 |
| `docx`／`pdf`／`pptx`／`xlsx` | Word、PDF、簡報、試算表的讀寫與製作 | 「讀這份 PDF 幫我摘要」「把這些資料做成簡報」 |
| `markitdown` | 各種文件格式轉 AI 易讀的 Markdown | 「把這個檔案轉成 markdown」 |
| `speak-human-tw` | 繁中潤稿：修 AI 腔、中國用語、半形標點 | 「這段公告幫我去 AI 味」 |

## 規劃與檢核

| 技能 | 功能 | 可以這樣說 |
|---|---|---|
| `brainstorm` | 想法還模糊時，先釐清選項、決策與下一步 | 「/brainstorm 我想做一個記帳 app」 |
| `grilling`／`grill-me` | 動手前讓 AI 針對計畫的漏洞逐一提問 | 「烤問我這個計畫」 |
| `skill-creator` | 把自己的流程做成新技能 | 「幫我把這個流程做成一個 skill」 |

## 記憶系統與知識庫

AIOS 的記憶不是黑箱——全部是你電腦上看得到的 Markdown 檔，分兩層：

**`private/context/`：你的正式檔案**（只有經你確認的內容會寫進來）

- `me.md`——你是誰、背景、長期方向。
- `working_style.md`——你希望 AI 怎麼協作：回覆格式、語氣、先問還是先做。

**`private/memory/`：日常運作的記憶**

- `active-context.md`——目前做到哪、下一步是什麼；跨對話續作靠這個。
- `decisions.md`——你做過的重要決定與原因。
- `feedback.md`——你糾正過 AI 的事，避免重蹈覆轍。
- `inbox.md`——AI 觀察到但**還沒經你確認**的候選（例如「使用者好像偏好簡短回覆」）。
- `daily/`——每日工作紀錄。

運作規則：AI 自己觀察到的東西只能進 inbox 當候選，不能自行寫進你的正式檔案；
你明確說「記住這個」才會正式寫入。相關例句：

> 「記住：我的報告都要先給結論」（寫入偏好）
> 「整理一下記憶」（審查 inbox 候選，`review-memory`）
> 「你最近學到了我什麼？」（唯讀查看，不落檔）

**知識庫**（`knowledge/`，可直接用 Obsidian 開啟）

| 技能 | 功能 | 可以這樣說 |
|---|---|---|
| `update-wiki` | 文件歸檔進知識庫：分類、補連結、更新索引 | 「把這份文件歸檔進知識庫」 |
| `obsidian-vault` | 唯讀搜尋整理 Obsidian 筆記與連結 | 「從我的筆記找出關於 X 的內容」 |

## 調整與優化系統

這套系統的規則本身（`CLAUDE.md`、`AGENTS.md`、你的 Context）都是可以調的，
而且不用自己動手改檔案——直接找 AI 討論。它會先提出修改預覽，經你確認才落檔：

> 「檢查 CLAUDE.md 和 AGENTS.md 有沒有矛盾或重複的規則」
> 「我覺得你回覆太長了，幫我把這個偏好寫進 working_style.md，先給我看要寫什麼」
> 「我想加一條規則：對外文件都要先過 speak-human-tw。跟我討論放哪裡最合適」
> 「AGENTS.md 第 X 節這條規則實際上造成困擾，幫我分析改掉的影響」

原則：入口檔與 Context 的修改一律**先預覽、你確認才寫入**；AI 不會因為自己
覺得更好就擅自改規則。改壞了也沒關係——所有檔案都在 Git 裡，隨時可以回溯。

## 內容創作

影片系列用 HTML 渲染出 MP4，不需剪輯軟體（首次出片需 Node.js，AI 會引導）：

| 技能 | 功能 | 可以這樣說 |
|---|---|---|
| `product-launch-video` | 產品網址或 brief → 宣傳片（自動抓網站素材與品牌色） | 「用這個網址做一支 60 秒宣傳片」 |
| `faceless-explainer` | 文章、筆記、主題 → 說明影片 | 「把這篇文章做成說明影片」 |
| `music-to-video` | 音樂 → 卡點影片（自動節拍分析） | 「這首歌做一支卡點影片」 |
| `embedded-captions` | 真人影片上字幕（本機轉錄，字幕可被人物遮擋） | 「幫這支影片上字幕」 |
| `talking-head-recut` | 訪談／Podcast 影片加圖形包裝（下標、資料卡） | 「幫這支訪談加上圖卡包裝」 |
| `motion-graphics` | 10 秒內動態圖文：logo 動畫、數據跳動、動態字 | 「做一個 8 秒的 logo 動畫」 |
| `slideshow` | 互動式簡報 deck | 「把這份內容做成簡報 deck」 |
| `pr-to-video` | GitHub PR → 更新說明影片 | 「把這個 PR 做成 changelog 影片」 |
| `video-spec-builder` | 渲染前以訪談方式把想法整理成逐鏡頭分鏡表 | 「我想拍一支影片，幫我想清楚」 |
| `cards` | 筆記或網址 → IG／Threads 輪播圖卡 PNG | 「把這篇筆記做成 IG 圖卡」 |

（另含 `hyperframes` 入口與 core／animation／creative／cli／registry／keyframes／media-use／figma 等支援技能，由入口自動調度。）

## 投資理財

來自 Anthropic 官方 financial-services 套件（Apache-2.0）。版本自動依工具選擇：
Claude Code 載入官方 plugin（隨 marketplace 更新），Codex 使用內建資料夾版，功能相同。

| 技能 | 功能 | 可以這樣說 |
|---|---|---|
| `dcf-model`／`lbo-model`／`3-statement-model` | DCF、LBO、三表財務模型 | 「幫我對 TSLA 做 DCF 估值」 |
| `comps-analysis` | 同業可比公司分析與估值倍數 | 「建一份同業比較表」 |
| `audit-xls`／`clean-data-xls` | 試算表公式稽核、資料清理 | 「檢查我這個模型為什麼不平衡」 |
| `earnings-analysis`／`earnings-preview`／`model-update` | 財報分析、財報前瞻、模型更新 | 「整理 NVDA 這季財報重點」 |
| `initiating-coverage`／`sector-overview`／`competitive-analysis` | 個股研究報告、產業概覽、競爭格局 | 「幫我寫一份產業研究」 |
| `morning-note`／`catalyst-calendar`／`thesis-tracker`／`idea-generation` | 晨會筆記、催化劑日曆、投資論點追蹤、選股 | 「幫我列下季的財報行事曆」 |
| `xlsx-author`／`pptx-author`／`deck-refresh`／`ib-check-deck`／`ppt-template-creator` | Excel／簡報產出、換數字、投行級簡報 QC | 「幫我 QC 這份 pitch deck」 |

> 分析輸出僅供研究參考，不構成投資建議。

## 環境依賴（用到才需安裝，AI 會引導）

| 功能 | 依賴 |
|---|---|
| 影片渲染 | Node.js |
| 社群圖卡 | `npm install`（Playwright） |
| 會議錄音轉錄 | `ffmpeg`＋`pip install faster-whisper`＋首次下載模型約 3GB |
| 其他功能 | 無 |

完整技能清單與來源見 `.aios/manifest.md`；版本歷史見 [CHANGELOG.md](CHANGELOG.md)。
