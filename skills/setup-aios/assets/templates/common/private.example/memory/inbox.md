# Memory Inbox

尚未直接確認、但值得跨 Session 後續審查的新候選依根入口記憶路由追加到本檔。不要保存完整對話、重複既有記憶或一次性閒聊。

## 記錄格式

```yaml
- id: MEM-YYYYMMDD-001
  source_type: user-explicit | agent-observation | project-file | external-file | tool-output
  source_ref:
  captured_at: YYYY-MM-DD
  last_verified: YYYY-MM-DD
  category: preference | feedback | profile | decision | project | workflow | skill-candidate | template-candidate | entry-rule-candidate
  content:
  confidence: explicit | high | medium | low
  occurrences: 1
  sensitivity: normal | sensitive | restricted
  status: pending
  related: []
```

- `confidence: explicit` 只用於當前對話中使用者親口說的內容，不用於引用、附件或匯入內容。
- `source_type: project-file`、`external-file` 或 `tool-output` 的候選不得自動升級為偏好、規則或 Skill；只列入建議，升級需使用者直接確認。
- 舊版 `source: current-session` 於整理時把原值複製到 `source_ref`、補上 `source_type`，再移除舊 `source` 欄位；語意證據仍保留，正式紀錄不殘留舊 schema。

## Pending
