from collections import defaultdict

import pytest

from app.orchestration import (
    AgentProfile,
    ContextBudgetManager,
    PanelOrchestrator,
    PanelRunState,
    SentencePolicy,
    SessionStateMachine,
    TurnAction,
    TurnDecision,
    TurnScheduler,
)


def decision(expert_id, action, urgency):
    return TurnDecision(
        expert_id=expert_id,
        action=action,
        urgency=urgency,
        public_focus=f"{expert_id} 的公开关注点",
    )


def test_scheduler_uses_agent_intent_instead_of_array_order():
    scheduler = TurnScheduler()
    result = scheduler.choose(
        [
            decision("expert-a", TurnAction.SPEAK, 40),
            decision("expert-b", TurnAction.REBUT, 85),
            decision("expert-c", TurnAction.WAIT, 100),
        ],
        current_turn=3,
        last_spoken_turn={"expert-a": 2, "expert-b": 1, "expert-c": 0},
    )

    assert result is not None
    assert result.expert_id == "expert-b"


def test_fairness_guard_prevents_starvation_without_becoming_round_robin():
    scheduler = TurnScheduler(starvation_turns=4, starvation_bonus=35)
    decisions = [
        decision("frequent", TurnAction.SPEAK, 70),
        decision("quiet", TurnAction.RAISE_HAND, 48),
    ]

    early = scheduler.choose(
        decisions,
        current_turn=3,
        last_spoken_turn={"frequent": 2, "quiet": 1},
    )
    late = scheduler.choose(
        decisions,
        current_turn=8,
        last_spoken_turn={"frequent": 7, "quiet": 1},
    )

    assert early.expert_id == "frequent"
    assert late.expert_id == "quiet"


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("第一句。第二句！第三句？", "第一句。第二句！"),
        ("只有一句完整观点。", "只有一句完整观点。"),
        ("没有标点的简短观点", "没有标点的简短观点"),
    ],
)
def test_sentence_policy_limits_visible_utterance_to_two_sentences(source, expected):
    assert SentencePolicy().normalize(source) == expected


def test_state_machine_rejects_illegal_transition():
    machine = SessionStateMachine()

    assert machine.transition("admitted", "running") == "running"
    with pytest.raises(ValueError):
        machine.transition("completed", "running")


def test_context_budget_never_mixes_sessions():
    manager = ContextBudgetManager(max_messages=2)
    messages = [
        {"session_id": "one", "content": "one-1"},
        {"session_id": "two", "content": "two-secret"},
        {"session_id": "one", "content": "one-2"},
        {"session_id": "one", "content": "one-3"},
    ]

    context = manager.select("one", messages)

    assert [item["content"] for item in context] == ["one-2", "one-3"]
    assert "two-secret" not in str(context)


class ScriptedGateway:
    def __init__(self):
        self.round = 0
        self.calls = defaultdict(int)

    async def host_utterance(self, *, phase, state):
        self.calls[f"host:{phase}"] += 1
        if phase == "opening":
            return "欢迎来到圆桌。请各位先说明最关键的判断标准。"
        return "今天的分歧集中在效率与公平的边界。下一步应验证数据并明确责任。"

    async def expert_decision(self, *, expert, state):
        self.calls[f"decision:{expert.id}"] += 1
        urgency = {
            0: {"a": 35, "b": 92, "c": 55},
            1: {"a": 88, "b": 25, "c": 60},
        }.get(self.round, {"a": 20, "b": 15, "c": 10})[expert.id]
        if expert.id == "c" and self.round == 0:
            action = TurnAction.SUPPLEMENT
        elif expert.id == "b" and self.round == 0:
            action = TurnAction.REBUT
        else:
            action = TurnAction.SPEAK
        return decision(expert.id, action, urgency)

    async def expert_utterance(self, *, expert, decision, state):
        self.calls[f"utterance:{expert.id}"] += 1
        self.round += 1
        return f"{expert.name}提出第一点。{expert.name}补充第二点。第三句必须被截掉。"


@pytest.mark.asyncio
async def test_orchestrator_opens_selects_dynamic_speakers_and_concludes():
    gateway = ScriptedGateway()
    emitted = []
    state = PanelRunState(
        topic_id="topic-1",
        session_id="session-1",
        title="测试议题",
        host=AgentProfile("host", "主持人", "主持人", "中立", "#69E4CE", "host"),
        experts=[
            AgentProfile("a", "甲", "研究员", "谨慎", "#B49CFF"),
            AgentProfile("b", "乙", "产品负责人", "支持", "#F6C177"),
            AgentProfile("c", "丙", "律师", "质疑", "#FF8B9C"),
        ],
        status="admitted",
        max_turns=2,
    )
    orchestrator = PanelOrchestrator(gateway=gateway, event_sink=emitted.append)

    result = await orchestrator.run(state)

    assert result.status == "completed"
    assert [entry.speaker_id for entry in result.transcript] == ["host", "b", "a", "host"]
    assert all(SentencePolicy().count(entry.content) <= 2 for entry in result.transcript)
    assert emitted[0].event_type == "session.state"
    assert any(event.event_type == "expert.status" for event in emitted)
    assert gateway.calls["host:opening"] == 1
    assert gateway.calls["host:conclusion"] == 1


class FailingGateway(ScriptedGateway):
    async def expert_utterance(self, *, expert, decision, state):
        raise TimeoutError("simulated model timeout")


@pytest.mark.asyncio
async def test_orchestrator_restores_expert_state_after_failure():
    state = PanelRunState(
        topic_id="topic-1",
        session_id="session-1",
        title="测试议题",
        host=AgentProfile("host", "主持人", "主持人", "中立", "#69E4CE", "host"),
        experts=[AgentProfile("a", "甲", "研究员", "谨慎", "#B49CFF")],
        status="admitted",
        max_turns=1,
    )
    orchestrator = PanelOrchestrator(gateway=FailingGateway(), event_sink=lambda event: None)

    with pytest.raises(TimeoutError):
        await orchestrator.run(state)

    assert state.expert_states["a"] == "waiting"
    assert state.status == "failed"
