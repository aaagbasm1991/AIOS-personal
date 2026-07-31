# AIOS Manifest

- edition: personal
- version: 0.2.0
- created: 2026-07-30
- skills_mode: copy
- skills_link_type: copy
- skills_copy_signature: 9ee84d1b199114ad56d04ba70f002c0d26ed256d50b5e6dce729dd3bce1424ae
- upgrade_from:
- upgrade_to:
- upgrade_status: not-applicable
- unapplied_differences: none

## Installed Skills

| Skill | Source | Status | Notes |
|---|---|---|---|
| brainstorm | shared skill catalog | installed | portable copy |
| docx | shared skill catalog | installed | portable copy |
| pdf | shared skill catalog | installed | portable copy |
| pptx | shared skill catalog | installed | portable copy |
| xlsx | shared skill catalog | installed | portable copy |
| markitdown | shared skill catalog | installed | portable copy |
| skill-creator | shared skill catalog | installed | portable copy |
| speak-human-tw | shared skill catalog | installed | portable copy |
| obsidian-vault | setup-aios portable template | installed | portable copy |
| update-wiki | shared skill catalog | installed | portable copy |
| review-memory | shared skill catalog | installed | portable copy |
| sync-aios-global | shared skill catalog | installed | portable copy |
| setup-aios | Albert-Agent/shared-skills | installed | portable copy; 2026-07-31 依使用者要求加入 |
| install-aios | 本 AIOS 自建 | installed | 從 GitHub 抓取範本、補私人層、訪談、全域整合 |
| aios-doctor | 本 AIOS 自建 | installed | 唯讀健檢：雙入口漂移、Skills 簽章、記憶結構、MCP 清單、fresh-session 驗證 |
| aios-backup | 本 AIOS 自建 | installed | 整套 AIOS（含 private/、對話紀錄）備份到使用者自己的 GitHub 私有 repo；含還原流程 |
| journal | 本 AIOS 自建 | installed | 每日反思日誌五題引導，寫入 daily/，明日待辦同步 active-context 閉環 |
| aios-guide | 本 AIOS 自建 | installed | 唯讀顯示功能總覽與版本紀錄；Set up 完成後向新使用者展示 |
| hyperframes | heygen-com/hyperframes (Apache-2.0) | installed | HTML 渲染影片入口（上游完整版，含 LICENSE） |
| hyperframes-core / -animation / -creative / -cli / -registry / -keyframes | heygen-com/hyperframes (Apache-2.0) | installed | HyperFrames 領域技能 6 件 |
| product-launch-video / faceless-explainer / pr-to-video / motion-graphics / music-to-video / general-video / embedded-captions / slideshow / remotion-to-hyperframes | heygen-com/hyperframes (Apache-2.0) | installed | HyperFrames 工作流 9 件 |
| media-use / talking-head-recut / figma | heygen-com/hyperframes (Apache-2.0) | installed | HyperFrames 輔助技能 3 件 |
| cards | shared skill catalog (ISC) | installed | IG／Threads／X 輪播圖卡；已排除 node_modules 與 output，首次使用需 npm install |
| grilling / grill-me | shared skill catalog | installed | 計畫烤問——無情拷問設計找漏洞 |
| meeting-notes-reference | 使用者自製 | installed | 會議記錄結構化＋Breeze-ASR-25 本機轉錄（術語表為空白範本；需 ffmpeg 與 pip install faster-whisper，首次轉錄下載模型約 3GB） |
| 理財技能 21 件：dcf-model / lbo-model / 3-statement-model / comps-analysis / audit-xls / clean-data-xls / xlsx-author / pptx-author / ppt-template-creator / deck-refresh / ib-check-deck / competitive-analysis / earnings-analysis / earnings-preview / model-update / morning-note / catalyst-calendar / idea-generation / initiating-coverage / sector-overview / thesis-tracker | anthropics/financial-services (Apache-2.0) | installed | 自官方 plugin 抽出為雙工具共用資料夾技能；LICENSE 於 docs/licenses/；plugin 的 skill-creator 與既有同名技能衝突未收錄；.claude/settings.json plugin 綁定已移除 |
| video-spec-builder | feicaiclub (MIT) | installed | 蘇格拉底式分鏡訪談，產出 video-spec.md 交 hyperframes 渲染 |

## Missing or Optional Skills

| Skill | Reason | Suggested action |
|---|---|---|
