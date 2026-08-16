from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Literal, Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


@runtime_checkable
class LLMProvider(Protocol):
    async def complete(
        self, *, system: str, messages: list[Message], response_model: type[T] | None = None
    ) -> T | str: ...

    def stream(self, *, system: str, messages: list[Message]) -> AsyncIterator[str]: ...


@lru_cache
def get_llm_provider() -> LLMProvider:
    from careervector.config import get_settings

    settings = get_settings()
    if settings.llm_provider == "anthropic":
        from careervector.infra.llm.anthropic_provider import AnthropicLLMProvider

        return AnthropicLLMProvider()

    from careervector.infra.llm.deepseek_provider import DeepSeekLLMProvider

    return DeepSeekLLMProvider()
