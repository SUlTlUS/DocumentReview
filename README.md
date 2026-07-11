# RAG 文档审核系统

基于 FastAPI、Vue 和轻量 RAG 的合同审核实训项目。项目分两个里程碑：Day2 v1.0 基础原型与 Day3 v2.0 分层架构升级。

## 当前状态

Day2 v1.0 与 Day3 v2.0 均已完成。默认运行使用 Mock LLM/OCR；外部能力测试明确标记为 `PASS (Mock)`，真实密钥不进入仓库。

## 目录约定

- `backend/`：API、数据库、解析、RAG、审核与测试。
- `frontend/`：Vue 页面、API client 与浏览器测试。
- `docs/`：需求追踪、验收记录与对比报告。
- `SPEC.md`：实现唯一技术规范。

## 本地启动

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```

```powershell
cd frontend
npm ci
npm run dev
```

后端默认 `http://127.0.0.1:8000`，前端默认 `http://127.0.0.1:5173`。

默认配置可直接体验完整上传、审核和问答流程。启用 DeepSeek 前复制 `backend/.env.example` 为 `backend/.env`，设置 `LLM_PROVIDER=deepseek` 与 API Key。启用真实 OCR 时另行安装 `backend/requirements-ocr.txt` 并设置 `OCR_PROVIDER=paddle`。

验证命令与报告见 [Day3 验证](docs/day3-validation.md)、[架构说明](docs/day3-architecture.md) 和 [v1/v2 对比](docs/day3-v1-v2-comparison.md)。
