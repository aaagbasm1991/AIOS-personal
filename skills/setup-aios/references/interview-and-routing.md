# Setup 訪談與答案路由

使用同一套標準流程，不區分管理者與一般成員。每次只問一題，已從現有文件取得的答案跳過。

## 十個核心問題

1. 這套 AIOS 的名稱、公司版或個人版，以及主要使用語言是什麼？
2. 使用者的稱呼、主要角色、責任與經常處理的工作是什麼？
3. 最希望 AI 協助的三類任務是什麼？
4. 最常產出的文件、格式與品質標準是什麼？
5. 希望 AI 如何回答、推薦方案與回報重大改動？
6. 哪些低風險工作可以直接執行？
7. 哪些外部操作、資料變更或高影響工作一定要先詢問？
8. 哪些資訊可以提出記憶候選；哪些情況允許落檔；哪些敏感內容禁止保存或只限任務當下使用？
9. 是否使用 Obsidian、Git、Claude Code、Codex；外部 Vault 哪些範圍可讀？
10. 希望 AI 主動改善哪些體驗，例如避免重問、套用格式、追蹤專案或提出 Skill 建議？

回答太抽象時只追問一個具體例子。不要要求使用者理解 AIOS 內部資料夾。

## 版本追問

### 公司版

只在核心問題尚未涵蓋時追問：

- 公司或團隊的一段非機密摘要。
- 哪些內容可供團隊共用、只限本人、不得交給外部 AI。
- 常用專案、文件與協作位置。
- 主要團隊角色與利害關係人類型；預設不收聯絡方式、績效或個人評價。
- 公司共享事實與共識的統一重驗週期（正整數天），保存於 `shared/company/about-company.md`；未知時留空並把新鮮度視為未確認，不猜數字。

### 個人版

只在核心問題尚未涵蓋時追問：

- 目前最重要的目標與個人專案。
- 想改善的習慣或學習方向。
- 健康、財務、關係、家庭與日記是否需要額外排除。

## 答案目的地路由（不等於寫入授權）

| 答案 | 位置 | 是否進共同 Git |
|---|---|---|
| 語言、AI 工作原則、安全邊界、記憶協議 | 根目錄 `AGENTS.md`／`CLAUDE.md` | 是 |
| 明確身份、角色、長期方向與資料邊界 | `private/context/me.md` 與 edition Context | 否 |
| 已確認的回答、格式與協作偏好 | `private/context/working_style.md` | 否 |
| 身份／偏好的來源與採納紀錄 | `private/memory/profile.md`／`preferences.md` ledger（只留 provenance、狀態與 canonical path） | 否 |
| 個人禁忌與踩坑 | `private/context/what_not_to_do.md`、`private/memory/feedback.md` | 否 |
| 短期任務續作、阻塞與下一步 | `private/memory/active-context.md` | 否 |
| 個人／公司專案登記與高階狀態 | `private/context/personal/projects.md`／`private/context/work/active-projects.md`；詳細狀態由專案自己的狀態檔擁有 | 否 |
| 可供團隊共用的工作共識 | `shared/team-memory/` | 是；另確認可共用性 |
| 公司或個人正式知識 | `knowledge/` | 視版本 Git 規則；另確認可共用性 |
| Obsidian 與本機絕對路徑 | `.aios/local.md`、`private/connections/` | 否 |

使用者不必逐題選擇位置。表中位置只表示通過檔案產出 Gate 後的目的地，不構成寫入授權；所有目的地（包括 `private/`）都先預覽並取得本輪明確寫檔要求或確認。進入 `shared/`、`knowledge/` 或共同 Git 時再額外確認可共用性。

## AGENTS／CLAUDE 模板欄位

產生檔案時替換：

- `{{AIOS_NAME}}`
- `{{AIOS_EDITION}}`
- `{{AIOS_OWNER}}`
- `{{AIOS_LANGUAGE}}`
- `{{AIOS_PRIMARY_TASKS}}`
- `{{AIOS_WORKING_STYLE}}`
- `{{AIOS_ALWAYS_NEVER}}`
- `{{AIOS_EDITION_RULES}}`

不得留下未解析欄位。

### 欄位長度與內容限制

入口是每次載入的固定 Context，保持精簡；細節留在 Context 與 references，不要塞進入口：

- `{{AIOS_PRIMARY_TASKS}}`：最多 3 條精簡 bullet。
- `{{AIOS_WORKING_STYLE}}`：最多 4 條精簡且穩定的 setup-time mirror；完整且目前有效的偏好以 `private/context/working_style.md` 為唯一權威。偏好內容獲確認不等於授權修改檔案；之後只有使用者本輪明確要求更新入口，或核准兩份入口的精確預覽時，才同步修改。
- `{{AIOS_ALWAYS_NEVER}}`：只放非顯而易見、成本高的安全／相容規則，不重複入口其他段落已寫的通則。
- `{{AIOS_EDITION_RULES}}`：精簡的路由規則；細節放在 Context 與 references。

兩份入口的共同語意責任與允許差異見 [entry-policy.md](entry-policy.md)。

### 公司版規則

`{{AIOS_EDITION_RULES}}` 至少包含：

- 個人記憶只留在 `private/`，不進團隊 Git。
- 團隊共識的建議目的地是 `shared/team-memory/`；通過檔案產出 Gate 後，寫入前再確認可共用。
- 規格、會議、正式決策與分析放 `knowledge/`。
- 任何團隊成員都可提出內容，不增加審批 router；形成正式內容時記錄具有採納權限的 `confirmed_by` 與 `source_ref`。
- 公司機密、客戶個資、帳密與未授權資料不寫入記憶。

### 個人版規則

`{{AIOS_EDITION_RULES}}` 至少包含：

- 個人 Context 與記憶只留在 `private/`。
- 健康、財務、法律、關係與日記只讀任務必要範圍。
- 高風險建議要查核最新可靠來源並說明限制。
- 外部 Obsidian Vault 預設唯讀，不探索排除資料夾。
