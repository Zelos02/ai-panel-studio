from ..config import Settings
from .base import LLMProvider
from .fake import FakeLLMProvider
from .openai_compatible import OpenAICompatibleProvider


def build_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "fake":
        return FakeLLMProvider()
    return OpenAICompatibleProvider(
        api_key=settings.llm_api_key or "",
        base_url=settings.llm_base_url,
        model=settings.llm_model,
    )
