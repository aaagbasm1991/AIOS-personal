# Private Example

首次 setup 時以 create-if-missing 方式，把 `private.example/` 映射建立為 `<aios-root>/private/`。更新或升級 AIOS 時不得覆蓋既有私人資料。

記憶新增、更新、搬移、封存與報告依根入口記憶路由與 `review-memory` 自身規則處理。`review-memory` 只依賴已落檔記憶與目前實際可見的 Session，不假裝存取完整聊天歷史。

## 安全邊界

- `private/` 只代表不進共同 Git，**不是加密，也不是存取控制**。
- 不得保存密碼、token、OAuth／session 憑證、`.env` 或其他秘密。
- `normal`：一般偏好與專案脈絡可保存。
- `sensitive`：只保存任務必要的最小摘要。
- `restricted`：預設不保存正文，只留最小摘要或來源指標，或使用者明確指定的受保護位置。
