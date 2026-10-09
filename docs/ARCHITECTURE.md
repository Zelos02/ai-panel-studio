# AI Panel Studio 架构设计

## 1. 技术选择

- 前端：React、TypeScript、Vite。组件与状态模型明确，适合响应式单页应用。
- 后端：FastAPI、Pydantic、SQLAlchemy。适合显式 API 契约、异步 SSE 和严格模型校验。
- 数据库：SQLite。满足本地 MVP、可复现测试和低部署成本。
- 实时通道：SSE。讨论主要是服务端到浏览器的单向增量事件，协议简单且支持事件 ID。
- 测试：Pytest、Vitest、Playwright；真实模型通过 Provider 边界替换为 Fake/Mock。

## 2. 系统拓扑

```mermaid
flowchart LR
    U[Browser / React] -->|REST| API[FastAPI API]
    U <-->|SSE| STREAM[SSE Stream]
    API --> APP[Application Services]
    STREAM --> BUS[Session Event Hub]
    APP --> ORCH[Panel Orchestrator]
    ORCH --> LLM[LLM Provider Port]
    LLM --> FAKE[Deterministic Fake]
    LLM --> REAL[OpenAI-compatible API]
    APP --> REPO[Repositories]
    ORCH --> REPO
    BUS --> REPO
    REPO --> DB[(SQLite)]
```

REST 承担命令与快照读取；SSE 只承担指定 Session 的事件增量。数据库中的 `internal_events` 是断线恢复和审计的事实来源，内存 Event Hub 只用于低延迟通知。

## 3. 模块边界

### 前端

- `features/topics`：话题列表、创建、恢复。
- `features/panel`：阵容生成与确认。
- `features/studio`：Transcript、状态卡、分岔、总结与连接状态。
- `services/api`：REST Client。
- `services/events`：SSE 连接、重连、去重。
- `state`：以 topicId/sessionId 为 Key 的客户端状态，禁止使用单一全局 Transcript。

### 后端

- `domain`：实体、枚举、状态转换、调度规则。
- `schemas`：外部 API 与模型输出的 Pydantic Schema。
- `repositories`：持久化接口及 SQLite 实现。
- `services`：用例服务、事务边界、幂等策略。
- `orchestration`：主持人、专家代理、TurnScheduler、上下文预算。
- `llm`：Provider Port、真实适配器、Fake Provider、版本化 Prompt。
- `api`：REST/SSE、请求校验、错误映射。
- `events`：事件持久化、发布和按序回放。

## 4. 状态机

### Topic 状态

```mermaid
stateDiagram-v2
    [*] --> draft
    draft --> ready: 阵容生成并确认
    ready --> running: 场次开始
    running --> ready: 场次暂停/停止但未完成
    running --> completed: 主持人完成总结
    draft --> failed: 阵容生成不可恢复失败
    ready --> failed: 场次创建失败
    running --> failed: 编排不可恢复失败
    failed --> draft: 用户重试阵容
    failed --> ready: 用户重试场次
```

### PanelSession 状态

```mermaid
stateDiagram-v2
    [*] --> created
    created --> admitted: 锁定阵容
    admitted --> running: 用户启动
    running --> paused: 后续暂停/恢复能力预留
    paused --> running: start 可恢复预留状态
    running --> stopping: 用户停止或满足结束条件
    stopping --> completed: 主持人收尾并生成总结
    created --> failed
    admitted --> failed
    running --> failed
    paused --> failed
```

只有应用服务可以驱动状态转换；Repository 不包含业务转换逻辑。

## 5. 一次发言的事件流程

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant E as Expert Agents
    participant S as TurnScheduler
    participant L as LLM Provider
    participant D as SQLite/Event Store
    participant B as Browser via SSE

    O->>E: 提供当前会话上下文，请求独立行动决策
    E->>L: 结构化 TurnDecision 请求
    L-->>E: wait/speak/rebut/supplement + 公开关注点
    E-->>S: 候选决策
    S-->>O: 选择下一位（非固定轮询）
    O->>D: 写入 preparing 状态事件
    D-->>B: expert.status
    O->>L: 请求 1～2 句话发言
    L-->>O: UtteranceResult
    O->>O: Schema 与句数校验
    O->>D: 同一事务写 Transcript 与 append 事件
    D-->>B: transcript.append
    O->>D: 恢复 waiting 并判断知识分岔
    D-->>B: expert.status / branch.created
```

## 6. 会话隔离与并发

- 所有会话产物表都带 `session_id`；所有读取必须显式过滤。
- SSE Endpoint 同时校验 URL 的 `session_id` 与该 Session 所属 `topic_id`。
- 数据库对 `(session_id, sequence)` 建唯一约束，保证消息和事件顺序。
- 单个 Session 使用应用级锁串行写入可见发言；不同 Session 可并发运行。
- Event Hub 的订阅频道使用 `session:{uuid}`，禁止共享广播频道。
- 前端 Store 使用 `{topicId}/{sessionId}` 作为缓存键，切换时先关闭旧连接。

## 7. 上下文管理

每次模型调用只发送当前 Session 的上下文：主题、背景、已确认阵容、最近若干条 Transcript、滚动摘要和相关分岔。达到预算时将较旧发言压缩为内部上下文摘要，但不改写已保存 Transcript。不得把其他 Session 内容加入上下文。

## 8. 数据可见性边界

| 数据 | 持久化 | API/UI 可见 |
| --- | --- | --- |
| 发言正文、发言人公开资料 | 是 | 是 |
| waiting/preparing/speaking | 是 | 是 |
| 简短公开关注点 | 是 | 是 |
| TurnDecision action/urgency/target | 可作为内部事件 | 否 |
| Provider 原始响应 | 默认否 | 否 |
| 隐藏思维链 | 不请求、不保存 | 否 |
| 总结结构化中间结果 | 可内部保存 | 仅输出 naturalText |

## 9. 故障与恢复

- 模型非法输出：Schema 校验失败，有限修复重试；仍失败则产生安全错误事件并恢复专家状态。
- SSE 断开：事件先落库；客户端携带 Last-Event-ID 重连并补发。
- 重复请求：生成阵容、确认和启动接口支持幂等键或状态检查。
- 进程重启：MVP 不保证运行中的后台任务自动恢复；已持久化的 Transcript、分岔与已完成总结仍可读取。生产化需要启动时检查点与持久化任务队列。
- 总结失败：保留完整 Transcript；单独重试总结是后续计划，当前未暴露公开端点。

## 10. 安全边界

- 真实 Key 仅从后端进程环境读取。
- `.env`、SQLite 运行文件、日志和浏览器构建产物不得包含 Key。
- 错误响应使用稳定错误码，不返回堆栈、模型原始载荷或环境变量。
- 所有模型输出均视为不可信数据，先校验和限制长度再使用。
