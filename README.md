# AI Panel Studio

一个本地运行的 AI 圆桌讨论 Web App MVP。输入议题后，系统生成主持人与多位立场互补的虚拟专家；专家根据实时 Transcript 自主决定发言、补充或反驳，页面同步呈现专家状态、知识分岔和最终自然语言总结。

## 已实现能力

- 多话题创建、列表与历史恢复。
- 默认 4 位专家，可选 2～8 位。
- 主持人/专家阵容生成、generation 版本保护和确认入场。
- 主持人开场/收尾，专家并行判断发言意图，非固定轮询调度。
- 每条可见发言限制为 1～2 句话。
- SSE 增量更新、事件回放、心跳、断线重连和 eventId 去重。
- 独立专家状态窗口与公开关注点摘要，不请求或展示隐藏思维链。
- 讨论中实时知识分岔、会话内去重和来源发言定位。
- 讨论完成后的自然语言复盘；原始 JSON 不进入 UI。
- deterministic Fake Provider：无 API Key、无外网也能演示和测试。
- 5 组可重复导入的高质量预设话题与嘉宾阵容。

## 技术栈

| 层 | 选择 | 原因 |
| --- | --- | --- |
| 前端 | React 19、TypeScript、Vite | 适合实时状态驱动的响应式单页应用 |
| 后端 | FastAPI、Pydantic、SQLAlchemy | API 契约清晰，异步 SSE 与模型 Schema 校验方便 |
| 数据库 | SQLite | 本地 MVP 零运维、测试容易隔离 |
| 实时通信 | SSE | 主要为服务端向浏览器的单向增量事件 |
| 测试 | Pytest、Vitest、Playwright | 覆盖领域、API、事件流、组件和真实浏览器闭环 |

架构、ER 图和事件流程见 [架构设计](docs/ARCHITECTURE.md)、[数据模型](docs/DATA_MODEL.md)；REST/SSE 细节见 [API 契约](docs/API_CONTRACT.md)。

## 目录

```text
backend/                 FastAPI、领域编排、SQLite、LLM Provider、测试
frontend/                React UI、SSE Hook、组件测试与 Playwright 用例
docs/                    SDD、API、测试策略、Prompt 记录、验收矩阵
scripts/                 Windows 下的安装、启动和测试脚本
tests/e2e/               E2E 说明入口（实际用例位于 frontend/e2e）
AI_PANEL_STUDIO_PROMPTS.md  分阶段开发 Prompt 与版本记录
```

## 从零安装

要求：Python 3.13、Node.js 20+、npm。

在项目根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
Copy-Item .\backend\.env.example .\backend\.env
```

默认 `.env.example` 使用 `LLM_PROVIDER=fake`，无需 API Key。

也可以手动安装：

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r .\backend\requirements-dev.txt
Set-Location .\frontend
npm install
npx playwright install chromium
```

## 初始化数据库与样例数据

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\seed.ps1
```

Seed 可重复执行：已有同名预设话题会跳过。默认数据库位于 `backend/data/panel_studio.db`，不会提交到 Git。

## 本地运行

分别打开两个 PowerShell：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-backend.ps1
```

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-frontend.ps1
```

访问 `http://127.0.0.1:5173`。后端 API 文档位于 `http://127.0.0.1:8000/docs`。

演示流程：

1. 发起新讨论，填写主题、人数、目标和背景。
2. 查看或重新生成主持人与专家阵容。
3. 确认入场并启动讨论。
4. 观察专家状态、增量 Transcript 和实时知识分岔。
5. 讨论结束后查看自然语言总结。
6. 返回首页并重新打开话题，验证历史恢复。

## 配置真实模型

所有模型配置只能写在 `backend/.env` 或后端进程环境中：

```dotenv
LLM_PROVIDER=openai_compatible
LLM_API_KEY=replace-with-your-server-side-key
LLM_BASE_URL=https://your-provider.example/v1
LLM_MODEL=your-model-name
```

DeepSeek 等提供 OpenAI-compatible Chat Completions 接口的模型可通过同一适配层配置。模型名称与 Base URL 以实际供应商控制台为准。严禁把 `.env`、Key 或含 Key 的日志提交到仓库。

## 测试

运行全部检查：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test-all.ps1
```

或分别运行：

```powershell
$env:PYTHONPATH="$PWD\backend"
.\.venv\Scripts\python -m pytest .\backend\tests --basetemp .\.tmp\pytest

Set-Location .\frontend
npm test
npm run build
npm run test:e2e
```

E2E 会自动启动前后端、使用 Fake Provider 和 `.tmp` SQLite，不调用真实模型。

## 主要 API

- `GET/POST /api/v1/topics`
- `POST /api/v1/topics/{id}/panel:generate`
- `PUT /api/v1/topics/{id}/panel:admit`
- `GET /api/v1/topics/{id}/experts`
- `POST/GET /api/v1/topics/{id}/sessions`
- `POST /api/v1/sessions/{id}:start`
- `POST /api/v1/sessions/{id}:stop`
- `GET /api/v1/sessions/{id}/events`（SSE）
- `GET /api/v1/sessions/{id}/transcript`
- `GET /api/v1/sessions/{id}/branches`
- `GET /api/v1/sessions/{id}/summary`

## UI 设计方向

界面采用深色“数据演播厅”风格：桌面端为专家状态、Transcript、知识分岔三栏，各区域独立滚动；平板减少侧栏；手机聚焦 Transcript，并将总结浮层化。专家专属颜色在阵容卡、状态卡与发言记录之间保持一致。

## 测试账号

本 MVP 没有账号系统，不需要测试账号或密码。

## 已知限制与后续方向

- 后台讨论任务运行在单个 FastAPI 进程；生产扩展可迁移到持久化任务队列。
- 进程重启后的运行中场次需要更完整的恢复调度。
- SQLite 适合本地 MVP，不适合多节点高并发写入。
- 知识分岔目前支持定位来源，尚未自动创建子讨论。
- 可进一步加入 Prompt 版本分析、token/成本统计和人工编辑总结。

## 工程记录

- [完整分阶段 Prompt](AI_PANEL_STUDIO_PROMPTS.md)
- [实际 Prompt 执行记录](docs/PROMPT_LOG.md)
- [开发工作流复盘](docs/DEVELOPMENT_WORKFLOW.md)
- [需求验收矩阵](docs/ACCEPTANCE_MATRIX.md)
