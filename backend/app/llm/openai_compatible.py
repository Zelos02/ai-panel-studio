import json
import logging
from typing import Any

import httpx


logger = logging.getLogger("panel_studio.llm.provider")


class OpenAICompatibleProvider:
    def __init__(self, *, api_key: str, base_url: str, model: str, timeout: float = 45.0) -> None:
        if not api_key:
            raise ValueError("LLM_API_KEY is required for openai_compatible provider")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._client = httpx.AsyncClient(
            timeout=self._timeout,
            headers={"Authorization": f"Bearer {self._api_key}"},
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema_name: str,
    ) -> dict[str, Any]:
        payload = {
            "model": self._model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        response = await self._client.post(
            f"{self._base_url}/chat/completions", json=payload
        )
        response.raise_for_status()
        body = response.json()
        usage = body.get("usage", {})
        details = usage.get("prompt_tokens_details", {})
        cache_hits = usage.get("prompt_cache_hit_tokens", details.get("cached_tokens", 0))
        cache_misses = usage.get("prompt_cache_miss_tokens")
        logger.info(
            "llm_usage schema=%s model=%s prompt_tokens=%s cache_hit_tokens=%s cache_miss_tokens=%s completion_tokens=%s",
            schema_name,
            self._model,
            usage.get("prompt_tokens"),
            cache_hits,
            cache_misses,
            usage.get("completion_tokens"),
        )
        content = body["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            raise ValueError(f"{schema_name} response must be a JSON object")
        return parsed
