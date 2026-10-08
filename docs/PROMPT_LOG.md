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
- 对应提交：待本阶段验收后填写。
