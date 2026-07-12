# RAG 文档审核系统

基于 FastAPI、Vue 和轻量 RAG 的合同审核实训项目。项目分两个里程碑：Day2 v1.0 基础原型与 Day3 v2.0 分层架构升级。

## 目录约定

- `backend/`：API、数据库、解析、RAG、审核与测试。
- `frontend/`：Vue 页面、API client 与浏览器测试。
- `docs/`：需求追踪、验收记录与对比报告。
- `SPEC.md`：实现唯一技术规范。

## 本地启动

首次使用 Windows 时，双击根目录的 `setup_env.cmd` 可一键安装环境。即使尚未安装 Python 或 Node.js，脚本也会优先通过 WinGet 安装 Python 3.11 与 Node.js LTS，再创建后端虚拟环境并安装前端依赖；已有 `backend/.env` 会被保留。脚本根据 Windows 地区、界面语言和时区判断中国区：中国区在本次安装中使用清华 PyPI 与 npmmirror，其他地区使用官方源，不修改用户全局 npm/pip 配置。可用 `setup_env.cmd --region cn` 或 `setup_env.cmd --region global` 手动覆盖判断。需要真实 PaddleOCR 时执行 `setup_env.cmd --with-ocr`，默认不会下载体积较大的 OCR 依赖。

Windows 下可直接双击根目录的 `run_local.cmd`。脚本会启动前后端、等待健康检查通过，然后自动打开默认浏览器。启动窗口会持续托管本次创建的服务；关闭窗口或按 `Ctrl+C` 会同时关闭对应前后端进程。脚本不会终止启动前已经存在的 8000/5173 服务。运行日志位于 `output/`。

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
