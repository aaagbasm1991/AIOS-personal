# Git 與衝突安全規則

## 寫入前

1. 執行 `git status --short`。
2. 記錄開始前已有的修改；它們屬於使用者，不納入本次 commit。
3. 確認 repository remote 是預期的私人團隊 repo；不因缺少 remote 自動建立公開 repo。
4. 確認目前 branch。預設流程使用 `main`，但不自動切換。

## Stage 與 commit

- 使用明確檔案清單，例如 `git add -- path/a.md path/b.md`。
- 路徑含空白或特殊字元時正確引用。
- 禁止 `git add -A`、`git add .`、`git commit -am`。
- commit 訊息建議：`wiki: ingest <type> <id>`。

## Pull 與 push

- 本機 commit 完成後才詢問是否同步。
- 使用者同意後執行 `git pull --rebase`。
- 衝突時停止；不要自動選 ours/theirs，不要改寫正式決策正文。
- 解決衝突後重新顯示 diff，再詢問是否 push。
- push 是外部狀態變更，必須每次取得明確同意。

## 衝突紀錄

衝突頁必須寫明：

- 發現日期。
- 涉及 ID 與檔案。
- 衝突類型：內容矛盾、模糊連結、重複 ID、來源缺失、敏感或授權風險。
- AI 看見的候選或差異。
- `decision: pending`。

敏感、restricted、客戶個資或授權風險的衝突頁只記錄遮蔽後的 ID、敏感分級與來源指標，不引用正文、不保存外部絕對路徑，也不把必要細節複製到 `private/` Markdown。需要查看的正文留在原核准來源系統，由工作人員依權限處理。

工作人員判斷後可直接把 `decision` 改成結果，並由 `update-wiki` 更新正式連結。不得加入額外審批人或核准狀態。
