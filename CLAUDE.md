# 项目说明

## 沟通与工作流

- 使用中文汇报，先读 PRD/SPEC 和当前代码，再修改。
- 复杂改动先计划；每个小步骤完成验证后单独 Git commit。
- 不把 Mock 结果描述为真实 DeepSeek 或真实 OCR 质量。

## 技术栈

- Backend：Python 3.11、FastAPI、SQLAlchemy 2、SQLite、Pydantic 2。
- Frontend：Vue 3、Vite、TypeScript、Tailwind CSS。
- Tests：pytest、Vitest、Playwright。

## 编码规范

- Python 使用类型注解、snake_case、SQLAlchemy 2 `Mapped` 写法；服务通过依赖注入获得 DB、LLM 和 OCR。
- Vue 组件使用 PascalCase 与 Composition API；API 类型集中定义。
- 用户可见错误包含原因和恢复动作；日志禁止输出合同全文、API Key 或聊天原文。

## 必须保持的契约

- 对外始终只有 SPEC 中列出的 9 个 HTTP 端点。
- Day3 升级不得破坏 Day2 前端请求与响应主字段。
- 原始 PRD、Day2、Day3 Markdown 作为需求输入，不做改写。

## 验证命令

- Backend：`python -m pytest -q`
- Frontend：`npm run typecheck`、`npm run test:unit`、`npm run build`
- E2E：`npm run test:e2e`
- Structure：`codegraph status`

## 红线

- 不读取、提交或打印 `.env` 中的秘密。
- 不自动 push、rebase、reset --hard 或删除用户未提交内容。
- 不提交数据库、uploads、模型缓存、node_modules、虚拟环境或测试输出。

