import json

from ..orchestration import AgentProfile, PanelRunState, TurnAction, TurnDecision
from .contracts import TurnDecisionContract, UtteranceResult
from .prompts import EXPERT_UTTERANCE_SYSTEM, HOST_UTTERANCE_SYSTEM, TURN_DECISION_SYSTEM
from .validated import ValidatedLLMClient


def _public_context(state: PanelRunState, limit: int = 24) -> str:
    rows = (
        {
            "sequence": message.sequence,
            "speakerId": message.speaker_id,
            "speakerRole": message.speaker_role,
            "content": message.content,
        }
        for message in state.transcript[-limit:]
    )
    return "\n".join(
        json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows
    )


class LLMAgentGateway:
    def __init__(self, client: ValidatedLLMClient) -> None:
        self.client = client

    async def host_utterance(self, *, phase: str, state: PanelRunState) -> str:
        result = await self.client.call(
            UtteranceResult,
            system_prompt=HOST_UTTERANCE_SYSTEM,
            user_prompt=(
                f"话题：{state.title}\n阶段：{phase}\n"
                f"公开 Transcript：{_public_context(state)}"
            ),
        )
        return result.content

    async def expert_decision(
        self, *, expert: AgentProfile, state: PanelRunState
    ) -> TurnDecision:
        result = await self.client.call(
            TurnDecisionContract,
            system_prompt=TURN_DECISION_SYSTEM,
            user_prompt=(
                f"话题：{state.title}\n专家：{expert.name}\n职业：{expert.title}\n"
                f"立场：{expert.stance}\n公开 Transcript（JSONL，按时间追加）：\n{_public_context(state)}"
            ),
        )
        return TurnDecision(
            expert_id=expert.id,
            action=TurnAction(result.action),
            urgency=result.urgency,
            public_focus=result.publicFocus,
            target_message_id=result.targetMessageId,
        )

    async def expert_utterance(
        self,
        *,
        expert: AgentProfile,
        decision: TurnDecision,
        state: PanelRunState,
    ) -> str:
        result = await self.client.call(
            UtteranceResult,
            system_prompt=EXPERT_UTTERANCE_SYSTEM,
            user_prompt=(
                f"话题：{state.title}\n专家：{expert.name}\n职业：{expert.title}\n"
                f"立场：{expert.stance}\n行动：{decision.action.value}\n"
                f"公开关注点：{decision.public_focus}\n"
                f"公开 Transcript（JSONL，按时间追加）：\n{_public_context(state)}"
            ),
        )
        return result.content
