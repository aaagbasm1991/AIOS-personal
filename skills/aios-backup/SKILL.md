---
name: aios-backup
description: >
  把整套 AIOS——含 private/ 記憶、workspace/、skills 與 AI 工具的專案對話
  紀錄——完整備份到使用者自己的 GitHub 私有 repo，並可從備份還原到新電腦。
  當使用者提到備份 AIOS、備份記憶、backup、怕資料不見、換電腦前先備份、
  還原備份時使用。絕不推送到 AIOS 範本的原始 repo。
---

# AIOS Backup — 完整備份到你自己的私有 repo

AIOS 的共用層（skills、docs、入口檔）由範本 repo 版控，但你的
`private/` 記憶、`workspace/` 工作區與 AI 對話紀錄**只存在這台電腦**。
本 Skill 把這些連同整個 AIOS 打包，備份到**你自己的 GitHub 私有 repo**。

## 鐵則

1. **只推到使用者自己的帳號**。備份 repo 與 AIOS 範本來源（`git remote -v`
   的 origin）必須是不同 repo；任何情況下不得把備份內容推回範本 repo。
2. **備份 repo 必須是 private**。建立後以 `gh repo view --json visibility`
   驗證；已存在的目標 repo 若是 public，停止並要求使用者更換或轉私有。
3. **憑證絕不進備份**：`.env`、token、auth／session／credential 檔、
   OAuth 快取一律排除。發現疑似憑證檔案時列出路徑請使用者確認處理。
4. 對話紀錄可能含敏感內容——納入前明確告知並取得同意（見第 3 步）。
5. 還原永不覆蓋現有檔案；衝突時保留兩份讓使用者比對。

## 備份流程

### 1. 確認目標 repo

- 檢查 `gh auth status`；未登入先請使用者登入。
- 詢問備份 repo 名稱（預設 `aios-backup`）。不存在則
  `gh repo create <name> --private`；存在則驗證 visibility 與擁有者。
- 驗證與 AIOS 範本 origin 不同源後才繼續。

### 2. 建立備份工作區

備份採「鏡像資料夾＋獨立 git」而非動 AIOS 本身的 git 設定：

- 位置：`<aios-root>/../<aios-folder-name>-backup/`（首次 clone 備份 repo，
  之後重用）。
- 每次備份時同步整個 AIOS 根目錄到備份資料夾，**包含** `private/`、
  `workspace/`、`.aios/local.md`（即共用 `.gitignore` 排除的個人層），
  但排除：`.git/`、`node_modules/`、`__pycache__/`、快取與輸出目錄、
  鐵則 3 的憑證類檔案。
- 備份 repo 自己的 `.gitignore` 只排除憑證與快取，不排除 private/。

### 3. 對話紀錄（詢問後納入）

告知使用者：「要一併備份 AI 工具的專案對話紀錄嗎？裡面是你和 AI 的完整
對話，可能包含敏感內容；備份 repo 是私有的，但仍要你確認。」同意後：

- Claude Code：`~/.claude/projects/` 底下**對應這個 AIOS 專案**的資料夾
  （名稱為專案路徑編碼），複製到備份的 `conversations/claude/`。
- Codex：`~/.codex/sessions/` 中屬於本專案的紀錄（可辨識時），複製到
  `conversations/codex/`。無法辨識歸屬就整批列出讓使用者挑選。
- 只複製對話 jsonl／markdown，不碰兩工具的 auth、settings、cache。

### 4. 提交與推送

- `git add -A`、commit（訊息含日期與摘要，例如
  `backup: 2026-08-01 full snapshot`）、push。
- 推送前最後檢查一次 remote 指向使用者自己的私有 repo。
- 回報：備份了幾個檔案、多大、repo 網址、上次備份距今多久。

### 5. 建議節奏

完成後提醒：重大工作階段結束或每週備份一次即可；也可以請 AI
「每次 session 結束提醒我備份」（寫入偏好，經確認後生效）。

## 還原流程（新電腦）

1. 先用 `install-aios` 裝好 AIOS 骨架（或 clone 範本）。
2. `gh repo clone <使用者>/<備份repo>` 到暫存位置。
3. 把備份中的 `private/`、`workspace/`、`.aios/local.md` 複製回 AIOS
   對應位置——**只補缺少的檔案**；兩邊都有且內容不同時，保留現有檔並把
   備份版放旁邊（`*.from-backup.md`）讓使用者比對。
4. 對話紀錄還原是選配：Claude Code 的專案對話放回
   `~/.claude/projects/` 對應資料夾即可在歷史中看到；不確定就先不還原，
   備份裡隨時能翻閱。
5. 還原後跑 `aios-doctor` 驗證，並開新對話確認 AI 記得 Context。

## 定期檢查

備份也會壞。每次備份時順帶驗證：上次 commit 時間、備份 repo 仍為
private、抽查 `private/context/me.md` 存在於備份中。異常就回報。
