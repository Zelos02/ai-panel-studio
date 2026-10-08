from __future__ import annotations

import asyncio
import json
import logging
from time import perf_counter
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from .base import LLMProvider

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger("panel_studio.llm")


def _contract_instruction(contract: type[BaseModel]) -> str:
    schema = json.dumps(
        contract.model_json_schema(by_alias=True),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return (
        "\n\n必须严格返回一个符合下列 JSON Schema 的 JSON 对象。"
        "字段名、类型、枚举、数量和格式约束都必须满足；不要添加 Markdown 代码块或额外文字。\n"
        f"JSON Schema：{schema}"
    )


def _validation_field_paths(error: ValidationError) -> str:
    paths: list[str] = []
    for item in error.errors(include_url=False, include_input=False):
        path = ".".join(str(part) for part in item["loc"])
        if path and path not in paths:
            paths.append(path)
    return ", ".join(paths[:12])


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
        contract_prompt = f"{system_prompt}{_contract_instruction(contract)}"
        repair_instruction = ""
        for attempt in range(1, self.max_attempts + 1):
            started = perf_counter()
            try:
                raw = await asyncio.wait_for(
                    self.provider.complete_json(
                        system_prompt=f"{contract_prompt}{repair_instruction}",
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
                fields = _validation_field_paths(exc) if isinstance(exc, ValidationError) else ""
                repair_instruction = (
                    "\n\n上一次响应未通过契约校验。请根据原始任务完整重写 JSON，"
                    "不要只返回局部修补内容。"
                    + (f"需要修正的字段路径：{fields}。" if fields else "请逐项核对全部 Schema 约束。")
                )
                logger.warning(
                    "llm_call_failed schema=%s attempt=%s error_type=invalid_output fields=%s",
                    contract.__name__,
                    attempt,
                    fields or "unavailable",
                )
                if attempt == self.max_attempts:
                    raise last_error from exc
        raise last_error or LLMContractError("unknown LLM contract failure")
