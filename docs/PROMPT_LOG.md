# 核心 Prompt 执行记录

本文件只记录实际执行过的阶段和真实修正。完整的当前 Prompt 规范见项目根目录 `AI_PANEL_STUDIO_PROMPTS.md`。

## 记录 1：SDD——产品规格、数据模型与 API 契约

### 实际 Prompt

> 检查空仓库，将测试题要求整理为 MVP 产品规格；定义 Topic、Expert、PanelSession、TranscriptMessage、ExpertStatus、KnowledgeBranch、InternalEvent、SessionSummary；设计 SQLite 表、状态机、REST/SSE 契约、可见性边界和测试追踪矩阵。本阶段只创建设计文档，不实现完整业务代码。

### 意图与过程

先固定业务不变量、实时事件和会话隔离边界，避免后续让模型一边写 UI 一边猜数据结构。当前仓库为空，没有遗留技术冲突；设计中特别把“公开关注点摘要”和隐藏思维链分开，并规定总结只向 UI 暴露自然语言。

### 结果

- 生成产品规格、架构、数据模型、API 契约和测试策略。
- 建立需求 ID 与测试追踪矩阵。
- 对应提交：`96286eb docs: define panel studio SDD and API contracts`

## 记录 2：基础工程——前后端骨架、SQLite 与 Provider 边界

### 实际 Prompt

> 按 SDD 契约建立 React/Vite 前端、FastAPI/SQLAlchemy 后端、完整 SQLite 实体、话题 CRUD、统一错误结构，以及可替换的 OpenAI-compatible/Fake LLMProvider；所有测试默认离线运行。

### 意图与过程

先把存储、HTTP 和模型调用边界固定下来，让后续 UI 与编排器可以分别迭代。实际遇到 Windows 沙箱无法解析含中文用户名的系统临时目录，以及 SQLite 读取时间后丢失时区的问题；通过把测试临时目录固定到项目内、在 API Schema 统一补齐 UTC 时区，并修正 Vitest/TypeScript 配置完成验证。

### 结果

- 后端 4 个测试通过，前端 1 个测试通过，前端生产构建成功。
- 真实 Key 只由后端配置读取，默认 Fake Provider 可离线工作。
- 对应提交：`9d109a0 feat: scaffold backend persistence and model provider`

## 记录 3：DDD——响应式演播厅视觉系统

### 实际 Prompt

> 使用模拟数据实现中文首页、创建话题弹窗、阵容/状态信息和三栏演播厅；桌面端区域独立滚动，窄屏合理降级；Transcript 不渲染内部事件，加入键盘焦点、ARIA 与 reduced-motion 支持。

### 意图与过程

先把产品信息层级和“演播厅感”做出来，再接真实 API，避免业务开发完成后才发现界面无法承载专家状态、长 Transcript 和实时分岔。实现采用无远程字体依赖的深色数据演播厅视觉，并将话题卡、专家栏、Transcript、知识分岔和创建面板拆成独立组件。

### 结果

- 前端 2 个交互/公开内容测试通过，生产构建成功。
- 桌面端采用三栏独立滚动；平板隐藏分岔侧栏；手机聚焦 Transcript 主舞台。
- 清理由 TypeScript 构建产生、误进入上一次提交的中间文件，并加入忽略规则。
- 对应提交：`4561ba8 feat: build responsive panel studio interface`

## 记录 4：DDD——真实话题、阵容生成与确认入场

### 实际 Prompt

> 接入话题 API，由后端 Provider 生成并严格校验主持人和专家阵容；Topic 持久化递增 generation，确认时拒绝旧版本；用户确认后锁定阵容、创建 PanelSession 并进入等待开场的演播厅。

### 意图与过程

把上一阶段的模拟界面替换为真实持久化业务闭环。实现时发现原数据模型遗漏了 API 契约已使用的阵容 generation，因此先将 Prompt 文档升级为 v1.1、同步补充数据模型，再用过期版本测试证明旧阵容无法被误确认。

### 结果

- 后端 7 个测试通过，覆盖生成、重新生成、过期版本、确认锁定和唯一活动场次。
- 前端 2 个集成测试通过，生产构建成功；已接入话题列表、创建、生成、确认和场次创建。
- 对应提交：`57dce9f feat: add topic and expert admission workflow`

## 记录 5：TDD——自主发言编排器

### 实际 Prompt

> 先写测试覆盖非固定轮询、自主行动、饥饿保护、1～2 句限制、状态机、会话上下文隔离和异常复位；确认红灯后，再实现 PanelOrchestrator、HostAgent、ExpertAgent、TurnScheduler、SentencePolicy 和 ContextBudgetManager。

### 意图与过程

把最容易被“一段循环轮流说话”糊弄过去的核心逻辑放到纯领域层，用可重复的脚本化 Gateway 证明调度结果由专家决策、紧迫度和反驳/补充意图决定。测试最初按预期因 `app.orchestration` 不存在而失败；实现后同一批测试转绿，并额外验证模型超时时 speaking 状态一定恢复为 waiting。

### 结果

- 编排器专项 9 个测试通过，完整后端 16 个测试通过。
- 主持人开场/收尾、专家并行决策、动态选人、短发言、停止条件和失败状态均有明确边界。
- 对应提交：`37aaa45 feat: implement tested autonomous panel orchestration`

## 记录 6：TDD——模型契约、有限重试与 Agent Gateway

### 实际 Prompt

> 将选角、专家行动、主持人/专家发言、知识分岔和总结拆成版本化 Prompt 与严格 Pydantic Schema；实现超时、取消、格式错误和有限重试，并用 LLMAgentGateway 适配领域编排器，禁止请求隐藏思维链。

### 意图与过程

模型输出被视为不可信输入，任何结果必须先通过独立契约才能进入领域层。实现采用最多 3 次的硬上限、可配置超时和安全日志；Fake Provider 同时实现全部契约，使核心回归测试不依赖网络或真实 Key。

### 结果

- 后端完整 21 个测试通过，覆盖首次非法后修复、持续非法、超时、Fake 契约和 Gateway 专家身份绑定。
- 阵容生成也统一接入 ValidatedLLMClient，不再绕过有限重试层。
- 对应提交：`10cbfb5 feat: add validated LLM adapters and prompt contracts`

## 记录 7：实时通信——SSE、事件持久化与前端增量更新

### 实际 Prompt

> 将 PanelOrchestrator 事件先写入 SQLite，再发布到按 Session 隔离的 EventHub；SSE 支持递增 eventId、回放、心跳和去重。前端用 EventSource 增量更新专家状态与 Transcript，切换页面时关闭旧连接。

### 意图与过程

采用“数据库是事实来源、内存 Hub 只负责低延迟通知”的方式，让浏览器断线后仍能回放。新增启动 API 测试时发现同步 FastAPI 路由运行在工作线程，无法创建 asyncio 后台任务；将端点改为异步路由后，任务正确绑定应用事件循环并通过回归。

### 结果

- 后端 24 个测试通过，覆盖后台启动、事件顺序、公开 Transcript、SSE 帧和跨会话隔离。
- 前端 3 个测试通过，生产构建成功；SSE Hook 覆盖连接、重复 eventId 过滤和关闭清理。
- 对应提交：`1607b80 feat: stream panel discussion events with SSE`

## 记录 8：业务闭环——知识分岔、总结与历史恢复

### 实际 Prompt

> 每条专家发言落库后立即调用 BranchSuggestion，按会话内指纹去重并发布 branch.created；讨论完成后调用 SessionSummaryResult，数据库可保存结构化中间结果，但 SSE/API/UI 只暴露 naturalText。重新进入话题时恢复最新场次、Transcript、分岔和总结。

### 意图与过程

将分岔判断放在持久化事件流水线中，保证它引用的是已经存在的 Transcript message ID，也能在总结前实时出现。总结事件发布前主动剥离 structured 数据，前端只接收自然语言；历史场次恢复则并行读取 Transcript 与分岔，并把未生成总结的 404 当作正常运行态处理。

### 结果

- 后端 24 个测试通过；新增断言证明分岔在 completed 事件之前出现、重复建议被去重、summary.ready 只含 naturalText。
- 前端 3 个测试通过并成功构建；已支持恢复历史讨论、实时分岔、结束控制和自然语言总结面板。
- 对应提交：`244fba1 feat: add knowledge branches summaries and topic isolation`

## 记录 9：E2E——真实浏览器闭环与异常恢复

### 实际 Prompt

> 使用 Playwright 自动启动 FastAPI 与 Vite，采用独立 SQLite 和 Fake Provider，完成创建话题、阵容确认、实时讨论、分岔、总结、返回首页和历史恢复；另模拟模型生成 504，验证安全中文错误且不泄露堆栈或 Key。

### 意图与过程

端到端测试只验证真实用户能观察到的闭环，把模型非法 Schema、SSE 重复事件和跨会话隔离留给更确定的单元/集成层。Playwright 使用无界面 Chromium 与本地服务，完整流程无需真实模型或网络 API。

### 结果

- 2 个 Playwright 场景全部通过，主流程约 6 秒完成并成功恢复历史总结。
- 需求验收矩阵将每项产品要求映射到实现与自动化证据。
- 对应提交：`b9bbcdf test: cover panel studio workflow end to end`

## 记录 10：交付——种子数据、运行文档与最终审计

### 实际 Prompt

> 为项目补充至少 5 组高质量讨论话题与完整嘉宾阵容，提供可复制的安装、启动、配置、种子和测试说明；执行后端、前端、生产构建、真实浏览器与移动端全量回归，完成安全扫描和最终交付审计。

### 意图与过程

最后阶段不再扩张业务范围，而是验证新环境能否复现项目、所有题目要求是否有证据。回归时发现 Vitest 默认扫描到了 `e2e` 下的 Playwright 文件，导致两个测试框架互相干扰；通过将 Vitest 的收集范围限定为 `src/**/*.test.{ts,tsx}` 修复，并重新运行全部检查。Prompt 规范没有变化，故保持 v1.1；这一实现层修正记录在本执行日志中。

### 结果

- 种子命令在独立 SQLite 数据库成功创建 5 个话题、5 位主持人和 20 位立场不同的专家，并由自动化测试验证幂等性。
- 后端 25 项、前端组件 3 项、Playwright 3 项全部通过；生产构建成功，移动端以 390 × 844 视口验收无横向溢出。
- 扫描未发现 `sk-...` 形式的真实密钥；API Key 仍只从后端环境变量读取。
- 对应提交：`0aec7f3 docs: add seed data delivery guide and final audit`
