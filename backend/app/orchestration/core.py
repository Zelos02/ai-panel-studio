from __future__ import annotations

import asyncio
import inspect
import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Awaitable, Callable, Protocol


class TurnAction(StrEnum):
    WAIT = "wait"
    RAISE_HAND = "raise_hand"
    SUPPLEMENT = "supplement"
    REBUT = "rebut"
    SPEAK = "speak"


@dataclass(frozen=True)
class AgentProfile:
    id: str
    name: str
    title: str
    stance: str
    color: str
    kind: str = "expert"


@dataclass(frozen=True)
class TurnDecision:
    expert_id: str
    action: TurnAction
    urgency: int
    public_focus: str
    target_message_id: str | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.urgency <= 100:
            raise ValueError("urgency must be between 0 and 100")
        if len(self.public_focus) > 300:
            raise ValueError("public_focus must not exceed 300 characters")


@dataclass(frozen=True)
class TranscriptEntry:
    session_id: str
    sequence: int
    speaker_id: str
    speaker_role: str
    content: str


@dataclass(frozen=True)
class OrchestrationEvent:
    event_type: str
    session_id: str
    payload: dict[str, Any]


@dataclass
class PanelRunState:
    topic_id: str
    session_id: str
    title: str
    host: AgentProfile
    experts: list[AgentProfile]
    status: str
    max_turns: int
    transcript: list[TranscriptEntry] = field(default_factory=list)
    expert_states: dict[str, str] = field(default_factory=dict)
    turn_count: int = 0
    stop_requested: bool = False

    def __post_init__(self) -> None:
        for expert in self.experts:
            self.expert_states.setdefault(expert.id, "waiting")


class AgentGateway(Protocol):
    async def host_utterance(self, *, phase: str, state: PanelRunState) -> str: ...

    async def expert_decision(
        self, *, expert: AgentProfile, state: PanelRunState
    ) -> TurnDecision: ...

    async def expert_utterance(
        self,
        *,
        expert: AgentProfile,
        decision: TurnDecision,
        state: PanelRunState,
    ) -> str: ...


class SentencePolicy:
    _sentence_pattern = re.compile(r".*?[。！？!?](?=\s*|$)", re.S)

    def count(self, text: str) -> int:
        cleaned = text.strip()
        if not cleaned:
            return 0
        matches = self._sentence_pattern.findall(cleaned)
        remainder = self._sentence_pattern.sub("", cleaned).strip()
        return len(matches) + (1 if remainder else 0)

    def normalize(self, text: str) -> str:
        cleaned = " ".join(text.strip().split())
        if not cleaned:
            raise ValueError("visible utterance must not be empty")
        parts = self._sentence_pattern.findall(cleaned)
        remainder = self._sentence_pattern.sub("", cleaned).strip()
        if remainder:
            parts.append(remainder)
        return "".join(parts[:2]).strip()


class TurnScheduler:
    _action_bonus = {
        TurnAction.SPEAK: 0,
        TurnAction.RAISE_HAND: 5,
        TurnAction.SUPPLEMENT: 8,
        TurnAction.REBUT: 12,
    }

    def __init__(self, *, starvation_turns: int = 5, starvation_bonus: int = 30) -> None:
        self.starvation_turns = starvation_turns
        self.starvation_bonus = starvation_bonus

    def choose(
        self,
        decisions: list[TurnDecision],
        *,
        current_turn: int,
        last_spoken_turn: dict[str, int],
    ) -> TurnDecision | None:
        candidates = [decision for decision in decisions if decision.action != TurnAction.WAIT]
        if not candidates:
            return None

        def score(item: TurnDecision) -> tuple[int, int, str]:
            silent_for = current_turn - last_spoken_turn.get(item.expert_id, -1)
            fairness = self.starvation_bonus if silent_for >= self.starvation_turns else 0
            action = self._action_bonus.get(item.action, 0)
            return (item.urgency + action + fairness, item.urgency, item.expert_id)

        return max(candidates, key=score)


class SessionStateMachine:
    _allowed = {
        "created": {"admitted", "failed"},
        "admitted": {"running", "failed"},
        "running": {"paused", "stopping", "failed"},
        "paused": {"running", "stopping", "failed"},
        "stopping": {"completed", "failed"},
        "completed": set(),
        "failed": set(),
    }

    def transition(self, current: str, target: str) -> str:
        if target not in self._allowed.get(current, set()):
            raise ValueError(f"illegal session transition: {current} -> {target}")
        return target


class ContextBudgetManager:
    def __init__(self, *, max_messages: int = 16) -> None:
        self.max_messages = max_messages

    def select(self, session_id: str, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        isolated = [message for message in messages if message.get("session_id") == session_id]
        return isolated[-self.max_messages :]


class HostAgent:
    def __init__(self, profile: AgentProfile, gateway: AgentGateway) -> None:
        self.profile = profile
        self.gateway = gateway

    async def speak(self, phase: str, state: PanelRunState) -> str:
        return await self.gateway.host_utterance(phase=phase, state=state)


class ExpertAgent:
    def __init__(self, profile: AgentProfile, gateway: AgentGateway) -> None:
        self.profile = profile
        self.gateway = gateway

    async def decide(self, state: PanelRunState) -> TurnDecision:
        decision = await self.gateway.expert_decision(expert=self.profile, state=state)
        if decision.expert_id != self.profile.id:
            raise ValueError("gateway returned a decision for a different expert")
        return decision

    async def speak(self, decision: TurnDecision, state: PanelRunState) -> str:
        return await self.gateway.expert_utterance(
            expert=self.profile, decision=decision, state=state
        )


EventSink = Callable[[OrchestrationEvent], Awaitable[None] | None]


class PanelOrchestrator:
    def __init__(
        self,
        *,
        gateway: AgentGateway,
        event_sink: EventSink,
        scheduler: TurnScheduler | None = None,
        sentence_policy: SentencePolicy | None = None,
    ) -> None:
        self.gateway = gateway
        self.event_sink = event_sink
        self.scheduler = scheduler or TurnScheduler()
        self.sentence_policy = sentence_policy or SentencePolicy()
        self.state_machine = SessionStateMachine()

    async def run(self, state: PanelRunState) -> PanelRunState:
        host = HostAgent(state.host, self.gateway)
        agents = {profile.id: ExpertAgent(profile, self.gateway) for profile in state.experts}
        last_spoken = {profile.id: -1 for profile in state.experts}

        try:
            state.status = self.state_machine.transition(state.status, "running")
            await self._emit(state, "session.state", {"status": state.status})
            await self._append_utterance(state, state.host, await host.speak("opening", state))

            while state.turn_count < state.max_turns and not state.stop_requested:
                decisions = list(
                    await asyncio.gather(*(agent.decide(state) for agent in agents.values()))
                )
                selected = self.scheduler.choose(
                    decisions,
                    current_turn=state.turn_count,
                    last_spoken_turn=last_spoken,
                )
                if selected is None:
                    break
                agent = agents[selected.expert_id]
                state.expert_states[selected.expert_id] = "preparing"
                await self._emit(
                    state,
                    "expert.status",
                    {
                        "expertId": selected.expert_id,
                        "state": "preparing",
                        "publicFocus": selected.public_focus,
                    },
                )
                state.expert_states[selected.expert_id] = "speaking"
                await self._emit(
                    state,
                    "expert.status",
                    {
                        "expertId": selected.expert_id,
                        "state": "speaking",
                        "publicFocus": selected.public_focus,
                    },
                )
                try:
                    utterance = await agent.speak(selected, state)
                    await self._append_utterance(state, agent.profile, utterance)
                finally:
                    state.expert_states[selected.expert_id] = "waiting"
                    await self._emit(
                        state,
                        "expert.status",
                        {
                            "expertId": selected.expert_id,
                            "state": "waiting",
                            "publicFocus": selected.public_focus,
                        },
                    )
                last_spoken[selected.expert_id] = state.turn_count
                state.turn_count += 1

            state.status = self.state_machine.transition(state.status, "stopping")
            await self._emit(state, "session.state", {"status": state.status})
            await self._append_utterance(
                state, state.host, await host.speak("conclusion", state)
            )
            state.status = self.state_machine.transition(state.status, "completed")
            await self._emit(state, "session.state", {"status": state.status})
            return state
        except Exception:
            for expert_id in state.expert_states:
                state.expert_states[expert_id] = "waiting"
            state.status = "failed"
            await self._emit(state, "session.state", {"status": "failed"})
            raise

    async def _append_utterance(
        self, state: PanelRunState, speaker: AgentProfile, content: str
    ) -> None:
        normalized = self.sentence_policy.normalize(content)
        entry = TranscriptEntry(
            session_id=state.session_id,
            sequence=len(state.transcript) + 1,
            speaker_id=speaker.id,
            speaker_role=speaker.kind,
            content=normalized,
        )
        state.transcript.append(entry)
        await self._emit(
            state,
            "transcript.append",
            {
                "sequence": entry.sequence,
                "speakerId": entry.speaker_id,
                "speakerRole": entry.speaker_role,
                "content": entry.content,
            },
        )

    async def _emit(
        self, state: PanelRunState, event_type: str, payload: dict[str, Any]
    ) -> None:
        result = self.event_sink(
            OrchestrationEvent(
                event_type=event_type,
                session_id=state.session_id,
                payload=payload,
            )
        )
        if inspect.isawaitable(result):
            await result
