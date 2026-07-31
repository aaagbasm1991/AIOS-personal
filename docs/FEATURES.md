# AIOS 個人版 — 功能總覽

把這個資料夾 clone 下來，從資料夾開啟 Claude Code 或 Codex，就得到一個
「記得你是誰、內建 59 個技能」的個人 AI 工作環境。

它與直接使用 AI 工具的差別：

- **有記憶**：你是誰、偏好怎麼協作、專案做到哪，寫在 `private/`（只存本機，不進 Git）。
- **技能開箱即用**：不用自己找 prompt 或裝擴充，說一句話就觸發對應流程。
- **可攜可分享**：一句話裝到新電腦；朋友 clone 後走訪談建立自己的版本。

各功能附「可以這樣說」的例句，照著講即可觸發。

## 開會與文件

**會議錄音整理**（`meeting-notes-reference`）

> 「幫我把這個錄音整理成會議記錄」

在本機轉逐字稿（Breeze-ASR-25，台灣國語＋中英夾雜特化，錄音不上傳雲端），
依術語表校正同音錯字，再整理成含決議、負責人、期限的結構化記錄。

**Office 與 PDF**（`docx`／`pdf`／`pptx`／`xlsx`／`markitdown`）

> 「讀這份 PDF 幫我摘要」「把這些資料做成簡報」「檢查這張報表的公式」

**繁中潤稿**（`speak-human-tw`）

> 「這段公告幫我去 AI 味，改自然一點再發」

修 AI 腔、中國用語與半形標點。

## 內容創作

**影片製作**（HyperFrames 系列，20 件）——用 HTML 渲染影片，不需剪輯軟體：

> 「用這個網址做一支 60 秒產品宣傳片」（`product-launch-video`）
> 「把這篇文章做成說明影片」（`faceless-explainer`）
> 「這首歌做一支卡點影片」（`music-to-video`）
> 「幫這支訪談影片上字幕」（`embedded-captions`，本機轉錄）
> 「做一個 8 秒的 logo 動畫」（`motion-graphics`）

想先確定腳本再渲染，可用 `video-spec-builder`：以訪談方式把想法逐鏡頭
整理成分鏡表，再交給 HyperFrames 出片。

**社群圖卡**（`cards`）

> 「把這篇筆記做成 IG 輪播圖卡」

輸出可直接發佈的 PNG（4:5 輪播或 1:1 方形）。

## 投資理財

估值建模（DCF／LBO／三表／comps）、試算表稽核、研究報告、財報分析、
簡報 QC 等 21 件，來自 Anthropic 官方 financial-services 套件（Apache-2.0）：

> 「幫我對 TSLA 做 DCF 估值」「整理 NVDA 這季財報重點」
> 「建一份同業比較表」「檢查我這個模型為什麼不平衡」

版本自動依工具選擇：Claude Code 載入官方 plugin（隨 marketplace 更新），
Codex 使用內建資料夾版，功能相同。分析輸出僅供研究參考，不構成投資建議。

## 規劃與檢核

**規劃模式**（`brainstorm`）——想法還模糊時先釐清選項與下一步：

> 「/brainstorm 我想做一個記帳 app」

**烤問模式**（`grilling`）——動手前讓 AI 針對計畫的漏洞逐一提問：

> 「烤問我這個計畫」

## 知識庫與記憶

- `knowledge/` 可直接用 Obsidian 開啟；說「把這份文件歸檔進知識庫」會自動分類、補連結、更新索引（`update-wiki`）。
- AI 觀察到的偏好只能作為候選，經你確認才寫入；說「整理一下記憶」可審查它記了什麼（`review-memory`）。

## 安裝與分享

裝到新電腦或分享給朋友，對方在 Claude Code 說：

> 「幫我從 https://github.com/aaagbasm1991/AIOS-personal 安裝 AIOS」

自動下載、建立私人層、訪談建立個人 Context，並詢問是否接入全域設定（`install-aios`）。

也可以把自己的流程做成新技能（`skill-creator`）：

> 「幫我把這個流程做成一個 skill」

## 環境依賴（用到才需安裝，AI 會引導）

| 功能 | 依賴 |
|---|---|
| 影片渲染 | Node.js |
| 社群圖卡 | `npm install`（Playwright） |
| 會議錄音轉錄 | `ffmpeg`＋`pip install faster-whisper`＋首次下載模型約 3GB |
| 其他功能 | 無 |

完整技能清單與來源見 `.aios/manifest.md`；版本歷史見 [CHANGELOG.md](CHANGELOG.md)。
