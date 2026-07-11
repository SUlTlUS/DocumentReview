# RAG 文档审核系统

基于 FastAPI、Vue 和轻量 RAG 的合同审核实训项目。项目分两个里程碑：Day2 v1.0 基础原型与 Day3 v2.0 分层架构升级。

## 当前状态

项目初始化阶段。默认验收使用 Mock LLM/OCR，真实密钥不进入仓库。

## 目录约定

- `backend/`：API、数据库、解析、RAG、审核与测试。
- `frontend/`：Vue 页面、API client 与浏览器测试。
- `docs/`：需求追踪、验收记录与对比报告。
- `SPEC.md`：实现唯一技术规范。

## 计划中的本地启动

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

