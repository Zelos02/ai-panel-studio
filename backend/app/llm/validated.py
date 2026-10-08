from __future__ import annotations

import asyncio
import logging
from time import perf_counter
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from .base import LLMProvider

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger("panel_studio.llm")


class LLMContractError(Exception):
    pass


class LLMInvalidOutput(LLMContractError):
    pass


class LLMCallTimeout(LLMContractError):
    pass


class ValidatedLLMClient:
    def __init__(
        self,
        provider: LLMProvider,
        *,
        timeout_seconds: float = 45.0,
        max_attempts: int = 2,
    ) -> None:
        if max_attempts < 1 or max_attempts > 3:
            raise ValueError("max_attempts must be between 1 and 3")
        self.provider = provider
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max_attempts

    async def call(
        self,
        contract: type[T],
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> T:
        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            started = perf_counter()
            try:
                raw = await asyncio.wait_for(
                    self.provider.complete_json(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        schema_name=contract.__name__,
                    ),
                    timeout=self.timeout_seconds,
                )
                result = contract.model_validate(raw)
                logger.info(
                    "llm_call schema=%s attempt=%s duration_ms=%s",
                    contract.__name__,
                    attempt,
                    round((perf_counter() - started) * 1000),
                )
                return result
            except asyncio.CancelledError:
                raise
            except asyncio.TimeoutError as exc:
                last_error = LLMCallTimeout(f"{contract.__name__} timed out")
                logger.warning(
                    "llm_call_failed schema=%s attempt=%s error_type=timeout",
                    contract.__name__,
                    attempt,
                )
                if attempt == self.max_attempts:
                    raise last_error from exc
            except (ValidationError, ValueError, KeyError, TypeError) as exc:
                last_error = LLMInvalidOutput(f"{contract.__name__} returned invalid output")
                logger.warning(
                    "llm_call_failed schema=%s attempt=%s error_type=invalid_output",
                    contract.__name__,
                    attempt,
                )
                if attempt == self.max_attempts:
                    raise last_error from exc
        raise last_error or LLMContractError("unknown LLM contract failure")
