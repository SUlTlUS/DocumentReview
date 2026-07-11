# 需求追踪矩阵

本文件在实施过程中持续更新。状态使用 `TODO`、`PASS`、`PASS (Mock)` 或 `FAIL`；Mock 只证明契约和编排，不代表真实模型质量。

| 来源 | 需求 | 实现位置 | 验证证据 | 状态 |
|---|---|---|---|---|
| PRD 2.1 | PDF/DOCX/TXT 上传、解析与索引 | `backend/app/services/parser.py`、`rag.py` | 三格式 pytest + upload API | PASS |
| PRD 2.2 | 列表、状态、删除及关联清理 | documents router + SQLAlchemy models | API integration | PASS |
| PRD 2.3 | 四维审核、风险等级、重复审核 | `backend/app/services/reviewer.py` | Mock reviewer tests | PASS (Mock) |
| PRD 2.4 | top-5 RAG、四轮历史、引用回答 | chat router + RAG service | Mock chat tests | PASS (Mock) |
| PRD 3.2 | 深色主题和 240px 侧栏 | `frontend/src` app shell + pages | unit test + Edge screenshot | PASS |
| Day2 | 五张表与 9 个端点 | models + routers | schema + OpenAPI inspection | PASS |
| Day2 | 四页路由和完整主流程 | Vue Router + four views | Edge desktop/mobile E2E | PASS |
| Day3 | 扫描 PDF OCR 降级 | 待实现 | Fake OCR contract | TODO |
| Day3 | YAML Prompt 可扩展维度 | 待实现 | dimension experiment | TODO |
| Day3 | 三阶段 LCEL 管线和日志 | 待实现 | pipeline tests | TODO |
| Day3 | API 与 Day2 兼容 | 待实现 | OpenAPI diff | TODO |
