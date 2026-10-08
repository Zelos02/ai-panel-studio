# AI Panel Studio API 契约

## 1. 通用约定

- Base URL：`/api/v1`
- Content-Type：`application/json; charset=utf-8`
- ID：UUID 字符串。
- 时间：UTC ISO-8601，例如 `2026-10-08T04:30:00Z`。
- 写请求可发送 `Idempotency-Key`；相同 Key 与相同资源返回首次结果。
- 所有响应携带 `X-Request-ID`；客户端也可提供该 Header。

成功响应直接返回资源或分页对象。错误响应统一为：

```json
{
  "error": {
    "code": "PANEL_INVALID_STATE",
    "message": "当前阵容尚未确认，无法开始讨论。",
    "requestId": "uuid",
    "retryable": false,
    "details": {}
  }
}
```

`details` 只包含安全的字段级提示，不含堆栈、环境变量、模型原始响应或内部 Prompt。

## 2. 公开资源 Schema

### Topic

```json
{
  "id": "uuid",
  "title": "AI 是否应该参与招聘终审？",
  "background": "可选背景",
  "goal": "可选讨论目标",
  "requestedExpertCount": 4,
  "status": "draft",
  "createdAt": "ISO-8601",
  "updatedAt": "ISO-8601"
}
```

### Expert

```json
{
  "id": "uuid",
  "kind": "expert",
  "name": "林澈",
  "title": "组织心理学研究员",
  "stance": "反对将最终决定完全自动化",
  "publicProfile": "关注公平性与候选人体验",
  "color": "#7C3AED",
  "displayOrder": 1,
  "admitted": false
}
```

### SessionSnapshot

包含 Session 基本状态、Topic 摘要、已确认阵容、专家状态、最近 Transcript、知识分岔和 `summaryNaturalText`。不得包含结构化总结原文、内部事件载荷、行动紧迫度或隐藏推理。

## 3. REST Endpoints

| 方法与路径 | 用途 | 主要状态码 |
| --- | --- | --- |
| GET `/topics` | 按更新时间倒序列出话题 | 200 |
| POST `/topics` | 创建话题 | 201, 422 |
| GET `/topics/{topicId}` | 话题详情及当前阵容/Session 摘要 | 200, 404 |
| POST `/topics/{topicId}/panel:generate` | 生成或重新生成未确认阵容 | 200, 409, 422, 502, 504 |
| PUT `/topics/{topicId}/panel:admit` | 原子确认当前阵容 | 200, 409 |
| GET `/topics/{topicId}/experts` | 获取主持人与专家 | 200, 404 |
| POST `/topics/{topicId}/sessions` | 基于已确认阵容创建 Session | 201, 409 |
| GET `/sessions/{sessionId}` | 获取完整公开快照 | 200, 404 |
| POST `/sessions/{sessionId}:start` | 启动或恢复讨论 | 202, 409 |
| POST `/sessions/{sessionId}:pause` | 暂停讨论 | 202, 409 |
| POST `/sessions/{sessionId}:stop` | 请求主持人收尾 | 202, 409 |
| POST `/sessions/{sessionId}/summary:retry` | 单独重试失败总结 | 202, 409 |
| GET `/sessions/{sessionId}/transcript` | 分页获取 Transcript | 200, 404 |
| GET `/sessions/{sessionId}/branches` | 获取知识分岔 | 200, 404 |
| GET `/sessions/{sessionId}/events` | SSE 实时流与回放 | 200, 404, 409 |

### POST `/topics`

请求：

```json
{
  "title": "AI 是否应该参与招聘终审？",
  "background": "公司计划引入自动化评估。",
  "goal": "评估效率、公平性和责任边界。",
  "requestedExpertCount": 4
}
```

校验：标题 1～200 字符；专家人数 2～8；超出限制返回 422。

### POST `/topics/{topicId}/panel:generate`

请求可为空对象。若话题已有 admitted 阵容则返回 409；若已有未确认阵容，使用 Idempotency-Key 避免重复生成。不返回 Provider 原始 JSON。

响应：

```json
{
  "topicId": "uuid",
  "generation": 2,
  "host": { "id": "uuid", "kind": "host", "name": "周岚", "title": "科技记者", "stance": "保持中立并检验论据", "publicProfile": "关注问题定义", "color": "#0EA5E9", "displayOrder": 0, "admitted": false },
  "experts": []
}
```

### PUT `/topics/{topicId}/panel:admit`

请求包含客户端看到的 `generation`，防止确认已被重新生成替换的旧阵容。成功后所有成员 `admitted=true`，Topic 进入 ready。

### POST `/topics/{topicId}/sessions`

请求：`{"maxTurns": 18}`。服务端校验阵容并创建 `created` 后立即进入 `admitted` 的 Session，同时建立每位专家的 waiting 状态。

### POST `/sessions/{sessionId}:start`

返回 202 与最新快照。重复 start 在已 running 时幂等返回当前资源；非法状态返回 409。

## 4. SSE 契约

Endpoint：`GET /api/v1/sessions/{sessionId}/events`

请求头可包含 `Last-Event-ID: 41`，也可在浏览器兼容场景使用 `?after=41`。服务端先按序回放 `sequence > 41` 的已持久化公开事件，再订阅实时频道。

帧示例：

```text
id: 42
event: transcript.append
data: {"eventId":42,"topicId":"...","sessionId":"...","timestamp":"...","payload":{"message":{"id":"...","speaker":{"id":"...","name":"林澈","title":"组织心理学研究员","color":"#7C3AED","role":"expert"},"sequence":7,"content":"效率提升不应掩盖偏差放大的风险。企业首先要证明评估标准本身是公平的。","createdAt":"..."}}}
```

公开事件：

| event | payload | UI 行为 |
| --- | --- | --- |
| `session.state` | status、turnCount | 更新控制状态 |
| `expert.status` | expertId、state、publicFocus | 更新单一专家卡 |
| `transcript.append` | message | 按 sequence 追加/去重 |
| `branch.created` | branch | 实时添加知识分岔 |
| `summary.ready` | naturalText | 显示自然语言总结 |
| `stream.error` | code、message、retryable | 显示安全错误与重试入口 |
| `heartbeat` | serverTime | 保持连接，不写入 Transcript |

每个 data 都包含 `eventId`、`topicId`、`sessionId`、`timestamp`、`payload`。前端必须校验 topicId/sessionId 并按 eventId 去重。

## 5. 分页与恢复

- `GET /topics?cursor=&limit=20`
- `GET /sessions/{id}/transcript?afterSequence=0&limit=100`
- 页面首次进入先获取 SessionSnapshot，再以其 `lastEventId` 建立 SSE，避免快照与订阅之间丢事件。
- 如果客户端请求的事件已超出保留范围，服务端返回 `stream.reset`（作为 SSE 控制事件）并要求重新获取快照。

## 6. 稳定错误码

| code | HTTP | retryable |
| --- | --- | --- |
| `VALIDATION_ERROR` | 422 | false |
| `RESOURCE_NOT_FOUND` | 404 | false |
| `PANEL_ALREADY_ADMITTED` | 409 | false |
| `PANEL_INVALID_STATE` | 409 | false |
| `SESSION_ALREADY_RUNNING` | 409 | false |
| `LLM_TIMEOUT` | 504 | true |
| `LLM_INVALID_OUTPUT` | 502 | true |
| `LLM_UNAVAILABLE` | 503 | true |
| `STREAM_REPLAY_REQUIRED` | 409 或 SSE reset | true |
| `INTERNAL_ERROR` | 500 | true |
