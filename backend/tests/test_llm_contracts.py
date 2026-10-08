import asyncio

import pytest

from app.llm import FakeLLMProvider, LLMAgentGateway, LLMCallTimeout, LLMInvalidOutput, ValidatedLLMClient
from app.llm.contracts import BranchSuggestion, SessionSummaryResult, TurnDecisionContract, UtteranceResult
from app.llm.prompts import BRANCH_SYSTEM, EXPERT_UTTERANCE_SYSTEM, SUMMARY_SYSTEM, TURN_DECISION_SYSTEM
from app.orchestration import AgentProfile, PanelRunState


class SequenceProvider:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = 0

    async def complete_json(self, **kwargs):
        self.calls += 1
        return next(self.responses)


@pytest.mark.asyncio
async def test_invalid_output_is_retried_then_validated():
    provider = SequenceProvider(
        [
            {"action": "invented", "urgency": 900, "publicFocus": "x"},
            {"action": "rebut", "urgency": 82, "publicFocus": "核对证据", "targetMessageId": None},
        ]
    )
    client = ValidatedLLMClient(provider, max_attempts=2)

    result = await client.call(
        TurnDecisionContract,
        system_prompt=TURN_DECISION_SYSTEM,
        user_prompt="测试",
    )

    assert result.action == "rebut"
    assert provider.calls == 2


@pytest.mark.asyncio
async def test_invalid_output_fails_after_bounded_attempts():
    provider = SequenceProvider([{}, {}])
    client = ValidatedLLMClient(provider, max_attempts=2)

    with pytest.raises(LLMInvalidOutput):
        await client.call(UtteranceResult, system_prompt=EXPERT_UTTERANCE_SYSTEM, user_prompt="测试")

    assert provider.calls == 2


class SlowProvider:
    async def complete_json(self, **kwargs):
        await asyncio.sleep(0.05)
        return {"content": "不会返回"}


@pytest.mark.asyncio
async def test_timeout_is_mapped_and_bounded():
    client = ValidatedLLMClient(SlowProvider(), timeout_seconds=0.005, max_attempts=1)

    with pytest.raises(LLMCallTimeout):
        await client.call(UtteranceResult, system_prompt=EXPERT_UTTERANCE_SYSTEM, user_prompt="测试")


@pytest.mark.asyncio
async def test_fake_provider_satisfies_all_public_contracts():
    client = ValidatedLLMClient(FakeLLMProvider())

    decision = await client.call(TurnDecisionContract, system_prompt=TURN_DECISION_SYSTEM, user_prompt="专家：甲")
    utterance = await client.call(UtteranceResult, system_prompt=EXPERT_UTTERANCE_SYSTEM, user_prompt="专家：甲")
    branch = await client.call(BranchSuggestion, system_prompt=BRANCH_SYSTEM, user_prompt="最新发言")
    summary = await client.call(SessionSummaryResult, system_prompt=SUMMARY_SYSTEM, user_prompt="完整讨论")

    assert decision.publicFocus
    assert utterance.content.count("。") <= 2
    assert branch.shouldCreate is True
    assert summary.naturalText and not summary.naturalText.lstrip().startswith("{")


@pytest.mark.asyncio
async def test_llm_gateway_returns_decision_for_requested_expert():
    gateway = LLMAgentGateway(ValidatedLLMClient(FakeLLMProvider()))
    expert = AgentProfile("expert-1", "林澈", "研究员", "关注公平", "#B49CFF")
    state = PanelRunState(
        topic_id="topic-1",
        session_id="session-1",
        title="测试议题",
        host=AgentProfile("host-1", "周岚", "主持人", "中立", "#69E4CE", "host"),
        experts=[expert],
        status="admitted",
        max_turns=1,
    )

    result = await gateway.expert_decision(expert=expert, state=state)

    assert result.expert_id == expert.id
    assert result.public_focus
