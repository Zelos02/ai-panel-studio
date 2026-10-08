# AI Panel Studio

一个本地运行的 AI 圆桌讨论 Web App MVP。输入议题后，系统生成主持人与多位立场互补的虚拟专家；专家根据实时 Transcript 自主决定发言、补充或反驳，页面同步呈现专家状态、知识分岔和最终自然语言总结。

## 已实现能力

- 多话题创建、列表与历史恢复。
- 讨论管理：双确认删除；未开场阵容可编辑且历史场次锁定。
- 默认 4 位专家，可选 2～8 位。
- 主持人/专家阵容生成、generation 版本保护和确认入场。
- 主持人开场/收尾，专家并行判断发言意图，非固定轮询调度。
- 每条可见发言限制为 1～2 句话。
- SSE 增量更新、事件回放、心跳、断线重连和 eventId 去重。
- 独立专家状态窗口与公开关注点摘要，不请求或展示隐藏思维链。
- 讨论中实时知识分岔、会话内去重和来源发言定位。
- 讨论完成后的自然语言复盘；原始 JSON 不进入 UI。
- Transcript 与长总结独立滚动，完成态明确显示为归档记录。
- deterministic Fake Provider：无 API Key、无外网也能演示和测试。
- 5 组可重复导入的高质量预设话题与嘉宾阵容。
- 窄屏使用四区域标签切换，成员、观点、知识分岔和总结不会因窗口缩小而丢失。
- 知识分岔区只展示真实分岔、冲突和待验证问题计数，不使用无数据来源的固定“收敛分数”。

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

## 交付物对应关系

| 测试题要求 | 对应文件或目录 | 说明 |
| --- | --- | --- |
| 完整项目源码 | `backend/`、`frontend/`、`scripts/` | 后端、前端、安装/运行/测试脚本 |
| 数据库初始化脚本 | `backend/app/database.py`、`scripts/seed.ps1` | 启动时建表；Seed 脚本可重复执行 |
| 至少 5 组高质量样例数据 | `backend/app/seed.py` | 5 个话题及各自主持人、4 位专家；`backend/tests/test_seed.py` 验证数量和幂等性 |
| 产品需求与验收标准 | `docs/PRODUCT_SPEC.md`、`docs/ACCEPTANCE_MATRIX.md` | MVP 范围、用户流程和逐项验收映射 |
| 架构与 Mermaid 图 | `docs/ARCHITECTURE.md` | 系统架构、状态机、时序图和故障边界 |
| 数据模型与 ER 图 | `docs/DATA_MODEL.md` | SQLite 表、约束、级联关系和 Mermaid ER 图 |
| API 文档 | `docs/API_CONTRACT.md` | REST、SSE、错误码与公开/内部数据边界 |
| 测试代码与策略 | `backend/tests/`、`frontend/src/*.test.tsx`、`frontend/e2e/`、`docs/TEST_STRATEGY.md` | Pytest、Vitest、Playwright |
| 运行、环境变量、技术选型、主要 API、已完成和后续方向 | `README.md` | 本文件相应章节 |
| 核心 Prompt 记录（不少于 5 段） | `AI_PANEL_STUDIO_PROMPTS.md`、`docs/PROMPT_LOG.md` | 12 个规范 Prompt、13 条实际执行/修正记录；明确包含 SDD、DDD、TDD、E2E |
| 开发过程与 AI 工作流说明 | `docs/DEVELOPMENT_WORKFLOW.md` | Codex/Claude Code 与 DeepSeek Provider 的协作方式、典型问题和工程化理解 |
| 最终交付审计 | `docs/FINAL_AUDIT.md` | 测试结果、交付物、边界和复现入口 |
| Git Commit 演进历史 | Git 仓库 `main` 分支与 GitHub Commits 页面 | 从文档/Schema、UI、测试到业务能力的分阶段提交 |

压缩包不包含 `.git`、`.env`、本地 SQLite、`.venv`、`node_modules`、`dist`、测试报告或临时文件；Git 历史以 GitHub 仓库为准。解压后先按下文执行安装和 Seed，即可生成本地数据库与样例数据。

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

Seed 可重复执行：已有同名预设话题会跳过。五组话题来自实际完成并人工确认质量的医疗责任、未成年人短视频、自动驾驶出租车、AI 独立开发者与企业 AI 用工圆桌；每组包含对应主持人和四位立场互补的专家。默认数据库位于 `backend/data/panel_studio.db`，不会提交到 Git。

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

如果页面提示“模型返回的专家阵容不完整”，先确认 `LLM_PROVIDER=openai_compatible` 并重启后端。后端日志会列出未通过契约的字段路径，但不会打印模型原文或 API Key。

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
E2E 默认使用 `18000` 和 `15173` 两个独立端口，因此日常开发服务器仍在运行时也可以执行。

## 主要 API

- `GET/POST /api/v1/topics`
- `POST /api/v1/topics/{id}/panel:generate`
- `PUT /api/v1/topics/{id}/panel`
- `PUT /api/v1/topics/{id}/panel:admit`
- `DELETE /api/v1/topics/{id}`
- `GET /api/v1/topics/{id}/experts`
- `POST/GET /api/v1/topics/{id}/sessions`
- `POST /api/v1/sessions/{id}:start`
- `POST /api/v1/sessions/{id}:stop`
- `GET /api/v1/sessions/{id}/events`（SSE）
- `GET /api/v1/sessions/{id}/transcript`
- `GET /api/v1/sessions/{id}/branches`
- `GET /api/v1/sessions/{id}/summary`

## UI 设计方向

界面采用深色“数据演播厅”风格：宽屏为专家状态、Transcript、知识分岔三栏，各区域独立滚动；视口不足 1180px 时改为成员、观点、分岔、总结四个标签，保留全部信息且不产生横向滚动。专家专属颜色在阵容卡、状态卡与发言记录之间保持一致。

## DeepSeek 缓存与调用成本

DeepSeek 的上下文缓存自动工作，关键是后续请求必须与既有请求拥有从首 token 开始完全一致的前缀。项目将逐轮 Transcript 编码为只追加的 JSONL，并把动态内容放在稳定身份信息之后；默认 18 轮讨论不会因滑窗删除旧消息而破坏前缀。真实 Provider 复用一个 HTTP Client，并在后端输出 `cache_hit_tokens`、`cache_miss_tokens` 和输出 Token，不记录 Prompt 原文或 API Key。

缓存命中率应按 `命中输入 /（命中输入 + 未命中输入）` 计算，不能把输出 Token 放进分母。缓存是尽力而为，首次请求和不同专家身份仍会产生未命中。

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
