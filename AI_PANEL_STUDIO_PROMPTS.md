# AI Panel Studio 分阶段开发 Prompt

> 用途：在 Codex/Claude Code 等 Vibe Coding 工作模式中，按阶段开发「AI 圆桌讨论 Web App MVP」。
>
> 使用方法：先阅读“公共前置 Prompt”，再一次只执行一个阶段。每阶段完成后运行测试、人工验收并创建独立 Git 提交，禁止一次性生成整个项目。

## Prompt 版本记录

| 版本 | 日期 | 变更 |
| --- | --- | --- |
| v1.0 | 2026-10-08 | 根据测试题要求建立 10 个分阶段 Prompt。 |

## Prompt 修改规则

1. 实际开发发现需求冲突、技术方案不可行或验收条件不完整时，先更新本文件，再修改实现。
2. 每次修改 Prompt，都在上方版本记录中写明日期、阶段、原因和影响。
3. 不得为了迁就已有代码而静默降低测试题要求。
4. `docs/PROMPT_LOG.md` 记录实际执行过的 Prompt、当时意图、真实问题和修正方式；本文件保存当前规范版本。

---

## 公共前置 Prompt

你正在迭代开发一个名为「AI Panel Studio」的本地 Web App MVP。

默认技术栈：

- 前端：React + TypeScript + Vite
- 后端：Python + FastAPI
- 数据库：SQLite
- 实时通信：优先使用 SSE
- 测试：Pytest、Vitest、Playwright
- 目录：`frontend`、`backend`、`docs`、`tests/e2e`

核心业务要求：

1. 用户可以创建和管理多个讨论话题，并设置专家人数，默认 4 人。
2. 系统根据话题生成主持人与专家阵容。专家必须包含姓名、职业或 Title、立场、专属颜色。
3. 用户确认阵容后才能进入演播厅。
4. 主持人负责开场、追问、串联和总结。
5. 专家根据最新 transcript 自主决定举手、抢答、补充、反驳或等待，不允许固定轮流发言。
6. 每次可见发言控制在 1～2 句话。
7. 每位专家拥有独立状态窗口，显示等待、准备发言、发言中，以及可公开的关注点摘要。不得展示或请求模型的隐藏思维链。
8. Transcript 只显示发言人姓名、职业或 Title、颜色和自然语言内容，不显示内部事件名称。
9. 讨论过程中实时产生知识分岔，而不是等讨论结束后统一生成。
10. 讨论结束后输出自然语言总结，严禁把 JSON 原文直接显示在页面上。
11. 不同话题的上下文、状态、事件、Transcript、知识分岔必须隔离。
12. API Key 只能由后端环境变量读取，禁止写入前端、数据库、日志或 Git。
13. 页面使用中文 UI，桌面端布局紧凑，普通桌面与窄屏布局合理；各主要区域可独立滚动。
14. 必须提供无真实 API Key 也能运行测试和演示的 deterministic fake LLM。
15. 保留已有正确实现，不重写无关代码，不覆盖用户未提交的修改。

每个阶段的工作方式：

- 开始前检查现有项目、Git 状态和已有文档。
- 只完成当前 Prompt 的范围，不提前一次性实现后续阶段。
- 重要业务逻辑先补测试或验收用例。
- 完成后运行相关检查，报告修改文件、测试结果、遗留问题和建议 Git commit。
- 不要在测试失败时声称阶段已经完成。
- 未经确认不要改写历史提交或合并提交。

---

## Prompt 1：【SDD】产品规格、数据模型与 API 契约

先检查当前仓库。如果仓库为空，只建立必要目录与设计文档，不要在本阶段实现完整业务代码。

请完成：

1. 将题目需求整理成明确的 MVP 功能范围、非功能要求和验收标准。
2. 定义核心领域对象：Topic、Expert、PanelSession、TranscriptMessage、ExpertStatus、KnowledgeBranch、InternalEvent、SessionSummary。
3. 设计 SQLite 数据表、字段、主外键、索引、时间字段和级联关系。
4. 用 Mermaid 绘制 ER 图、讨论会状态流转图、一次发言的事件流程图。
5. 定义 Topic、Session、Expert 等状态机和合法转换。
6. 编写 REST API 契约，覆盖话题、嘉宾生成与确认、讨论会、Transcript、知识分岔、总结和 SSE。
7. 定义 SSE 事件结构、事件 ID、会话隔离方式、断线恢复语义和错误结构。
8. 说明哪些数据只供内部编排使用，哪些允许出现在 Transcript 或 UI 中。
9. 给出测试策略和需求到测试的追踪矩阵。

生成或更新：

- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/DATA_MODEL.md`
- `docs/API_CONTRACT.md`
- `docs/TEST_STRATEGY.md`

验收条件：

- 每项题目要求都能映射到数据模型、API 或测试。
- 明确禁止展示隐藏思维链。
- API 契约能够支持增量更新和多话题隔离。
- Mermaid 图可以正常渲染。
- 本阶段不生成整套业务实现。

建议提交：`docs: define panel studio SDD and API contracts`

---

## Prompt 2：【基础工程】前后端骨架、SQLite 与模型适配层

读取 Prompt 1 的设计文档，按契约搭建最小可运行工程。

1. 创建前后端和 E2E 目录。
2. 后端按 domain、schemas、repositories、services、api、llm 分层。
3. 接入 SQLite，建立可重复执行的初始化或迁移方案。
4. 实现数据模型、Repository、健康检查和基础话题 CRUD API。
5. 建立统一 LLMProvider，支持 OpenAI-compatible Provider 和 deterministic FakeLLMProvider。
6. 测试默认使用 Fake Provider，不访问外部网络。
7. 后端环境变量包含 LLM_API_KEY、LLM_BASE_URL、LLM_MODEL、DATABASE_URL、LLM_PROVIDER。
8. 提供 `.env.example`，不得写入真实密钥。
9. 提供统一错误响应、日志和请求 ID，日志不得包含 Key。
10. 为初始化、Repository、配置和基础 API 编写测试。

验收：前后端可分别启动；SQLite 初始化可重复；无 Key 时 Fake Provider 可运行；Git 不包含密钥和本地数据库。

建议提交：`feat: scaffold backend persistence and model provider`

---

## Prompt 3：【DDD】演播厅视觉系统与响应式页面骨架

先用模拟数据完成前端设计，不实现完整 AI 编排。

1. 建立背景、面板、边框、字体、间距、专家颜色和状态视觉规范。
2. 实现话题首页、新建入口、进行中/已完成状态和最近更新时间。
3. 实现阵容确认页面，显示主持人、专家、Title、立场、颜色、重新生成和确认入场。
4. 实现演播厅骨架：Transcript、专家状态、知识分岔、控制与总结区域。
5. 桌面端紧凑分栏并独立滚动；窄屏使用堆叠、抽屉或 Tab。
6. 不显示举手、抢答等内部事件标签。
7. 加入键盘操作、ARIA、颜色对比度和 reduced-motion 支持。
8. 为关键组件和响应式状态编写测试。

验收：模拟数据可浏览完整 UI；长 Transcript 不拖动整个页面；窄屏无严重溢出；视觉效果像演播厅而非普通聊天窗口。

建议提交：`feat: build responsive panel studio interface`

---

## Prompt 4：【DDD】话题创建、嘉宾生成与确认入场

1. 接入话题读取、创建和切换 API。
2. 新建话题支持主题、默认 4 人的专家人数、可选背景和讨论目标。
3. 后端通过 LLMProvider 生成主持人与专家阵容。
4. 专家包含稳定 ID、姓名、职业或 Title、立场、颜色和公开简介。
5. 模型结果必须通过 Schema 校验后才能入库。
6. 支持生成失败、超时、格式错误、重试和取消。
7. 防止重复点击产生重复阵容。
8. 用户确认后锁定阵容并创建 PanelSession。
9. Fake Provider 返回稳定且观点不同的阵容。
10. 测试成功、失败、重复请求、非法人数和刷新恢复。

验收：完成“创建话题 → 生成阵容 → 确认入场”；未确认不能开始；话题之间不串数据；错误信息不显示堆栈或 JSON。

建议提交：`feat: add topic and expert admission workflow`

---

## Prompt 5：【TDD】讨论编排器与自主发言调度

先写失败测试，再实现代码。

1. 主持人负责开场、提问、追问、串联和收尾。
2. 专家读取最新 Transcript 后返回 wait、raise_hand、supplement、rebut 或 speak。
3. 编排器根据行动、紧迫度、目标和上下文选择下一位发言者。
4. 不允许按专家数组顺序机械轮流；公平性只防止长期饥饿。
5. 每条可见发言限制 1～2 句话，超限时重写或安全截断。
6. 同一时刻只允许一条可见发言进入 Transcript。
7. 每位专家拥有独立上下文和状态。
8. 不同 PanelSession 完全隔离。
9. 支持轮次、时间、用户停止和主持人结束条件。
10. 超时、异常和取消不会让状态卡死。

实现 PanelOrchestrator、HostAgent、ExpertAgent、TurnDecision、TurnScheduler、SessionStateMachine 和 ContextBudgetManager。内部事件不得显示在 Transcript，不得保存或展示隐藏思维链。

验收：测试证明发言不是固定轮询、会话隔离、发言长度合规、主持人流程自然，Fake Provider 测试确定可重复。

建议提交：`feat: implement tested autonomous panel orchestration`

---

## Prompt 6：【TDD】真实模型适配、Prompt 模板与结构化输出

1. 建立可版本化模板：嘉宾生成、专家决策、专家发言、主持人发言、分岔判断和总结。
2. 定义 GuestGenerationResult、TurnDecision、UtteranceResult、BranchSuggestion、SessionSummaryResult。
3. 校验无效 JSON、缺失字段、未知枚举、超长和空内容。
4. 对可恢复错误有限重试，禁止无限循环。
5. 实现超时、取消、速率限制、网络失败和 Provider 错误映射。
6. Provider 可替换，可配置 DeepSeek 或其他 OpenAI-compatible 模型。
7. API Key 只存在于后端环境变量。
8. 日志只记录请求 ID、耗时、模型名和错误类型。
9. 不请求 chain-of-thought，只请求结构化决定、公开摘要和答案。
10. 使用 Mock/Fake Provider 测试成功、格式错误、超时和重试。

验收：切换模型不改领域逻辑；格式错误不使讨论崩溃；输出入业务层前均经过校验；浏览器产物无 Key。

建议提交：`feat: add validated LLM adapters and prompt contracts`

---

## Prompt 7：【实时通信】SSE 事件流与前端增量更新

后端：

1. 讨论启动后在后台运行 PanelOrchestrator。
2. 提供 PanelSession 的 SSE Endpoint。
3. 支持 session.state、expert.status、transcript.append、branch.created、summary.ready、stream.error、heartbeat。
4. 每个事件包含 eventId、topicId、sessionId、timestamp 和 payload。
5. 支持 Last-Event-ID 或等效断线恢复。
6. 发送 heartbeat 并清理断开的订阅者。
7. 保证会话订阅隔离。

前端：

1. 连接当前会话事件流并实时更新发言、专家状态、分岔和总结。
2. 使用 eventId 去重。
3. 显示连接中、已连接、重连中和失败状态。
4. 页面卸载或切换话题时关闭旧连接。
5. SSE 事件名不得显示在 Transcript 中。

验收：逐条实时更新；短暂断线后不重不漏；切换话题不串流；包含事件流和重连测试。

建议提交：`feat: stream panel discussion events with SSE`

---

## Prompt 8：【业务闭环】知识分岔、总结与多话题管理

1. 每次发言后识别新概念、新假设、观点冲突、待验证问题和延伸方向。
2. 分岔在讨论过程中增量产生，关联来源 Transcript message ID。
3. 相似分岔去重或合并；UI 可定位来源发言。
4. 总结包含焦点、观点、分歧、共识、未决问题和下一步。
5. 前端只显示自然语言总结，解析失败时安全降级，禁止显示 JSON。
6. 首页展示多个话题状态和摘要。
7. 重新打开话题时恢复阵容、Transcript、分岔和总结。
8. 同时运行多个话题时完全隔离。
9. 已完成讨论默认只读，可明确新建 Session。

验收：分岔实时出现；总结自然可读；切换刷新后数据正确；并发话题隔离。

建议提交：`feat: add knowledge branches summaries and topic isolation`

---

## Prompt 9：【E2E】端到端测试、异常恢复与回归修复

使用 Playwright、deterministic Fake Provider 和临时 SQLite，不访问真实模型。

主流程覆盖：创建话题、默认 4 位专家、阵容校验、确认入场、启动讨论、主持人开场、专家状态、非固定轮流发言、Transcript 增量、实时分岔、自然语言总结、返回首页并恢复数据。

异常流程覆盖：嘉宾生成超时、非法结构、SSE 重连、事件去重、快速切换话题、中途停止、运行中刷新、后端异常不泄露堆栈或密钥。

执行全部后端、前端和 E2E 测试，修复浏览器控制台错误、未处理 Promise、无效网络请求和响应式问题。输出需求验收矩阵，列出每项要求对应的实现文件、测试和结果。

建议提交：`test: cover panel studio workflow end to end`

---

## Prompt 10：【交付】样例数据、文档、Prompt 记录与最终审计

1. 提供至少 5 个高质量预设话题，每个包含至少 4 位观点有差异的嘉宾，通过 Seed 脚本生成。
2. README 包含产品介绍、演示流程、技术栈、目录、运行、环境变量、Fake/真实模型、数据库、测试、API、ER 图、设计方向、限制和后续改进。
3. 创建 `docs/PROMPT_LOG.md`，至少记录 5 段实际使用过的核心 Prompt，覆盖 SDD、DDD、TDD、E2E；每段附 1～2 句真实意图、挑战和修正方式。
4. 创建约 1～1.5 页的 `docs/DEVELOPMENT_WORKFLOW.md`，说明 Claude Code/Codex 与实际模型的协作方式、2～3 个真实问题和工程化 AI 开发理解。
5. 最终审计 Git 历史、样例数据、ER/API 文档、测试、密钥安全、Transcript、思维链、总结 JSON、多话题隔离和从零运行流程。
6. 不得伪造开发记录或隐藏失败测试；最终阶段只修复具体问题，不进行无理由大重构。

建议提交：`docs: add seed data delivery guide and final audit`

---

## 每阶段实际记录模板

```text
阶段：
本轮目标：
实际使用的 Prompt：
AI 首次输出的问题：
我的修正指令：
最终结果：
对应 Git commit：
```
