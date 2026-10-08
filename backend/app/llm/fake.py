import hashlib
from typing import Any


class FakeLLMProvider:
    """Deterministic provider used by local development and automated tests."""

    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema_name: str,
    ) -> dict[str, Any]:
        digest = hashlib.sha256(
            f"{schema_name}\n{system_prompt}\n{user_prompt}".encode("utf-8")
        ).hexdigest()[:12]
        return {"schema": schema_name, "fixtureId": digest}
