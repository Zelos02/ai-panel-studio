# 需求验收矩阵

| 要求 | 主要实现 | 自动化证据 | 结果 |
| --- | --- | --- | --- |
| 话题列表与创建 | `services/api.ts`、topics API | `test_topics.py`、Playwright 主流程 | 通过 |
| 默认 4 人与人数校验 | `TopicCreate`、创建表单 | `test_topics.py` | 通过 |
| 动态主持人/专家阵容 | `PanelService`、PanelAdmission | `test_panels.py`、E2E 阵容计数 | 通过 |
| 旧阵容不可误确认 | `panel_generation` | `test_stale_generation_cannot_be_admitted` | 通过 |
| 主持人开场/收尾 | `PanelOrchestrator`、LLMAgentGateway | `test_orchestrator_opens_selects_dynamic_speakers_and_concludes` | 通过 |
| 专家自主、非固定轮询 | TurnDecision、TurnScheduler | 调度器优先级与饥饿保护测试 | 通过 |
| 发言 1～2 句话 | SentencePolicy | 参数化句数测试、持久化讨论测试 | 通过 |
| 独立专家状态 | ExpertStatus、expert.status | 异常复位与事件持久化测试 | 通过 |
| 实时 Transcript | EventStore、SSE、useSessionEvents | SSE 帧、后台启动、Hook 测试、E2E | 通过 |
| Transcript 不显示内部事件 | 公开事件投影 | 前端测试、讨论持久化测试 | 通过 |
| 实时知识分岔 | DiscussionEventPipeline | 分岔先于 completed 的断言、E2E | 通过 |
| 分岔去重 | session + fingerprint 唯一约束 | Fake 重复建议只产生一个分岔 | 通过 |
| 自然语言总结 | SessionSummaryResult、SummaryPanel | summary.ready 公开字段断言、E2E | 通过 |
| 多话题/会话隔离 | session_id 查询与独立频道 | `test_running_one_session_does_not_emit_into_another` | 通过 |
| SSE 断线恢复和去重 | Last-Event-ID、EventStore、客户端 eventId | EventStore 顺序、Hook 重复事件测试 | 通过 |
| 模型非法格式/超时 | ValidatedLLMClient、Pydantic JSON Schema 注入 | 重试、持续非法、超时、真实 Provider Schema 与字段纠错测试 | 通过 |
| 安全错误提示 | Error Handler、ApiError | 422 测试、E2E 504 测试 | 通过 |
| API Key 后端隔离 | Settings、Provider Factory | 默认 Fake 测试；仓库 `sk-...` 凭据扫描无结果 | 通过 |
| 响应式演播厅 | 三栏/平板/移动 CSS | 前端构建、390 × 844 Playwright 视口测试 | 通过 |
| 历史恢复 | sessions/transcript/branches/summary API | Playwright 完成后重新进入 | 通过 |
| 讨论删除 | Topic ORM cascade、运行态保护、双确认 UI | 级联删除测试、运行态 409、Playwright 管理场景 | 通过 |
| 未开场阵容编辑 | generation、成员 ID/人数/状态校验 | API 编辑/锁定测试、组件与 Playwright 管理场景 | 通过 |
| 长复盘可读性 | 固定比例中心网格、总结独立滚动 | Playwright 高度与 overflow 断言 | 通过 |
| Provider 缓存前缀 | JSONL 追加上下文、24 条默认窗口、连接复用 | 第二轮 Prompt 以前一轮为完整前缀的测试 | 通过 |

## E2E 场景

1. 真实浏览器主流程：创建话题、3 位专家、确认入场、启动讨论、实时完成、分岔、总结、返回首页、重新进入并恢复。
2. 模型生成超时：浏览器拦截生成 API 返回 504，页面展示可重试中文错误，不泄露堆栈或 Key。
3. 移动端布局：390 × 844 视口下首页无横向溢出，创建话题弹窗完整位于视口内。

SSE 重复事件、模型非法 Schema、并发会话隔离等难以稳定地由浏览器制造的异常，分别在前端 Hook 测试和后端集成测试中覆盖。
