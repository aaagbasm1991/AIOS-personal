# Memory Index

這是記憶導航，不保存完整正文。唯一固定啟動 Context 是平台原生載入的根入口；只有需要個人化、續作或跨 Session 資訊時才讀本檔，再依下表只讀對應葉節點。

| 記憶 | 檔案 | 何時讀取 |
|---|---|---|
| 回答與工作偏好 | `../context/working_style.md` | 回答格式、語氣或協作方式會影響結果時 |
| 近期任務與下一步 | `active-context.md` | 續作或跨 Session 任務時；只讀短期狀態，專案定義由 edition Context 或專案本身擁有 |
| AI 糾正與踩坑 | `feedback.md`、`../context/what_not_to_do.md` | 相似、重大改動或高風險任務前 |
| 穩定身份與長期方向 | `../context/me.md`、edition 專屬 Context | 使用者身份或長期目標與任務相關時 |
| 個人重要決定 | `decisions.md` | 涉及既有選擇時 |
| 尚未整理的記憶 | `inbox.md` | 記憶捕捉與整理時 |
| 身份／偏好 provenance | `profile.md`、`preferences.md` | 只有追溯來源或執行記憶整理時 |
| 整理狀態 | `review-state.md` | 記憶整理判斷或有落檔變化時 |
| 每日摘要 | `daily/` | 需要回顧特定日期時 |
| 記憶健檢 | `reviews/` | 追蹤改善建議時 |
| 過時內容 | `archive/` | 只有追溯需要時 |

不要在啟動時載入完整 `daily/`、`reviews/` 或 `archive/`。
