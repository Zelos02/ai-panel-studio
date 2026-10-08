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
- 对应提交：待本阶段验收后填写。

## 记录 2：基础工程——前后端骨架、SQLite 与 Provider 边界

### 实际 Prompt

> 按 SDD 契约建立 React/Vite 前端、FastAPI/SQLAlchemy 后端、完整 SQLite 实体、话题 CRUD、统一错误结构，以及可替换的 OpenAI-compatible/Fake LLMProvider；所有测试默认离线运行。

### 意图与过程

先把存储、HTTP 和模型调用边界固定下来，让后续 UI 与编排器可以分别迭代。实际遇到 Windows 沙箱无法解析含中文用户名的系统临时目录，以及 SQLite 读取时间后丢失时区的问题；通过把测试临时目录固定到项目内、在 API Schema 统一补齐 UTC 时区，并修正 Vitest/TypeScript 配置完成验证。

### 结果

- 后端 4 个测试通过，前端 1 个测试通过，前端生产构建成功。
- 真实 Key 只由后端配置读取，默认 Fake Provider 可离线工作。
- 对应提交：待本阶段验收后填写。
