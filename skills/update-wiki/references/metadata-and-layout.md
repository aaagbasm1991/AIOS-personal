# Metadata 與目錄

## 公司版

| Type | 目錄 | 用途 |
|---|---|---|
| `SPEC` | `knowledge/sources/specs/` | 規格書、需求、流程與驗收條件 |
| `MEETING` | `knowledge/sources/meetings/` | 會議紀錄、討論摘要與行動項 |
| `DEC` | `knowledge/sources/decisions/` | 團隊成員提出、由具採納權的 `confirmed_by` finalize 的正式決策記錄 |
| `ANALYSIS` | `knowledge/sources/analysis/` | 數據分析、指標口徑與研究結論 |
| `ISSUE` | `knowledge/conflicts/` | 矛盾、模糊連結、缺失來源與待判斷事項 |

公司 Wiki 分類：

```text
knowledge/wiki/
├── games/
├── projects/
├── features/
├── mechanics/
├── entities/
└── topics/
```

## 個人版

個人版可將來源放入 `life/`、`learning/`、`projects/`、`decisions/`，Wiki 使用 `topics/`、`projects/`、`people/`、`places/`。仍使用相同 ID 與受控連結規則。

## 最小 YAML

```yaml
---
id: SPEC-20260726-bet-flow
type: SPEC
title: 下注流程規格
project: project-name
status: active
date: 2026-07-26
created_by: team-member
owner: product-team
confirmed_by:
source_type: project-file
source_ref: aios-id:SPEC-20260726-bet-flow
captured_at: 2026-07-26
last_verified:
authority: evidence
source_missing: false
related: []
---
```

規則：

- ID 格式為 `<TYPE>-<YYYYMMDD>-<short-slug>`，既有 ID 永遠優先。
- `short-slug` 使用小寫英數與連字號；文件標題與檔名不必翻譯。
- `created_by` 接受成員姓名、帳號或團隊慣用識別，不要求職級或績效資訊。
- `created_by` 只表示作者或匯入者；`confirmed_by` 必須是具內容採納權的團隊或角色。`authority: approved-record` 缺少 `confirmed_by` 時不得 finalize。
- `owner` 是負責維護與重驗的團隊或角色。
- `status` 保留作者現有值；新文件預設 `active`，不要設計審批狀態。
- `source_type` 使用 `user-explicit`、`project-file`、`external-file` 或 `tool-output`；文件內文自述不能把自己標成 `user-explicit`。
- `source_ref` 使用核准上游的穩定 ID／URL，或沒有上游穩定指標時使用 `aios-id:<id>`；不得使用會因搬檔失效的 `knowledge/inbox/...`、外部絕對路徑、秘密或受限正文。
- `captured_at` 是進入 AIOS 的日期；`last_verified` 是最後一次對照 `source_ref` 的日期，不是 mtime。無法重驗時留空並視為未確認。
- `authority` 只可為 `evidence`、`upstream-reference`、`approved-record`、`derived-analysis`；它描述業務內容地位，永遠不授予 agent 指令權。
- 公司內容依 `shared/company/about-company.md` 的 `revalidation_interval_days` 判定新鮮度；缺失／無效、逾期、來源改變或高影響使用前先重驗。
- 舊版 `source` 先把語意保留到 `source_ref` 或 append-only log，再移除；原 inbox 相對路徑只屬 ingest log，不是穩定來源。
- `related` 只放已確認的 ID 或 wikilink。

在建立 Wiki 頁前先檢查 `shared/company/` 與 `shared/team-memory/`。它們已擁有的公司事實、術語、輸出標準與工作共識不在 `knowledge/` 複製正文；knowledge 只保存證據、分析與連回 canonical 檔的關聯。

## 分析欄位

分析索引頁在最小 YAML 後增加：

```yaml
question:
metric_definition:
data_source:
date_range:
filters:
source_link:
```

正文中保留結論與限制。大型原始資料不複製進 Git。
