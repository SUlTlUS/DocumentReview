# 需求追踪矩阵

本文件在实施过程中持续更新。状态使用 `TODO`、`PASS`、`PASS (Mock)` 或 `FAIL`；Mock 只证明契约和编排，不代表真实模型质量。

| 来源 | 需求 | 实现位置 | 验证证据 | 状态 |
|---|---|---|---|---|
| PRD 2.1 | PDF/DOCX/TXT 上传、解析与索引 | 待实现 | pytest + E2E | TODO |
| PRD 2.2 | 列表、状态、删除及关联清理 | 待实现 | API integration | TODO |
| PRD 2.3 | 四维审核、风险等级、重复审核 | 待实现 | Mock LLM tests | TODO |
| PRD 2.4 | top-5 RAG、四轮历史、引用回答 | 待实现 | Mock chat tests | TODO |
| PRD 3.2 | 深色主题和 240px 侧栏 | 待实现 | UI test + screenshot | TODO |
| Day2 | 五张表与 9 个端点 | 待实现 | schema + OpenAPI snapshot | TODO |
| Day2 | 四页路由和完整主流程 | 待实现 | Playwright | TODO |
| Day3 | 扫描 PDF OCR 降级 | 待实现 | Fake OCR contract | TODO |
| Day3 | YAML Prompt 可扩展维度 | 待实现 | dimension experiment | TODO |
| Day3 | 三阶段 LCEL 管线和日志 | 待实现 | pipeline tests | TODO |
| Day3 | API 与 Day2 兼容 | 待实现 | OpenAPI diff | TODO |

