# Day3 验证报告

## 自动化结果

| 验证项 | 结果 | 证据 |
|---|---|---|
| 后端单元/集成/API | PASS | 27 passed |
| 后端覆盖率 | PASS | 89% statements |
| 前端单元测试 | PASS | 4 passed |
| TypeScript 类型检查 | PASS | `vue-tsc -b` |
| 前端生产构建 | PASS | Vite 8 build |
| 前端生产依赖审计 | PASS | 0 vulnerabilities |
| Day2 九端点兼容 | PASS | OpenAPI method/path snapshot |
| 数字 PDF/DOCX/TXT | PASS | 真实 fixtures 解析与上传 |
| 扫描 PDF fallback | PASS (Mock) | 空文本 PDF → `ocr-mock` |
| DeepSeek LCEL | PASS (Mock) | 相同 Runnable/Prompt/校验契约 |
| YAML 六维实验 | PASS | `caab175`；随后 `afd30d7` 恢复五维 |

## 浏览器与 UI/UX 验收

在 Microsoft Edge 中重新执行 PDF 上传、首次审核、查看三项风险、进入问答并询问违约责任。页面显示管线 `v2.0`、耗时 22ms、3 项问题和 1 项高风险，回答包含命中文档原文。浏览器控制台为 0 error、0 warning。375×812 移动视口下，导航、标题、消息卡片和输入区没有横向溢出或控件遮挡。

最终视觉检查继续遵循 `ui-ux-pro-max` 的 Trust & Authority 方向。Kinetic Typography 只出现在标题、指标与加载反馈，使用 transform/opacity，不干扰合同长文本。实际模拟 `prefers-reduced-motion: reduce` 后，标题字符 animation 和 transition duration 均降为 `0.00001s`，静态回退通过。桌面审核页的信息顺序为总览 → 摘要 → 高风险 → 中风险，满足先扫风险再读证据的任务路径。

## 已知限制

- DeepSeek 未使用真实 API Key，真实准确率、成本、超时和限流尚未验收。
- PaddleOCR 重型依赖未安装，扫描件只验证 Fake Provider 契约；真实识别质量未验收。
- DOCX 通过 OOXML、解析和上传链路验证；本机缺少 LibreOffice，Word COM 导出无响应，因此没有完成 DOCX 页面视觉渲染。
- 系统仍是单用户训练原型，未包含身份认证、租户隔离、恶意文件沙箱或生产监控告警。
