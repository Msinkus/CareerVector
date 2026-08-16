from collections.abc import AsyncIterator
from typing import TypeVar

from anthropic import AsyncAnthropic
from anthropic.types import MessageParam
from pydantic import BaseModel

from careervector.config import get_settings
from careervector.core.exceptions import LLMResponseError
from careervector.infra.llm.client import Message

T = TypeVar("T", bound=BaseModel)

_MAX_TOKENS = 4096
_STRUCTURED_OUTPUT_TOOL = "emit_result"


class AnthropicLLMProvider:
    """LLMProvider backed by the Anthropic SDK.

    Structured output is implemented via forced tool-use (a single tool matching the
    response_model's JSON schema, with tool_choice pinned to it) rather than any
    provider-specific "response format" flag, since forced tool-use is the stable,
    generally-available mechanism for schema-constrained output on Claude models.
    """

    def __init__(self, model: str | None = None) -> None:
        settings = get_settings()
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = model or settings.anthropic_default_model

    async def complete(
        self, *, system: str, messages: list[Message], response_model: type[T] | None = None
    ) -> T | str:
        payload: list[MessageParam] = [{"role": m.role, "content": m.content} for m in messages]

        if response_model is None:
            response = await self._client.messages.create(
                model=self._model, system=system, max_tokens=_MAX_TOKENS, messages=payload
            )
            return "".join(block.text for block in response.content if block.type == "text")

        response = await self._client.messages.create(
            model=self._model,
            system=system,
            max_tokens=_MAX_TOKENS,
            messages=payload,
            tools=[
                {
                    "name": _STRUCTURED_OUTPUT_TOOL,
                    "description": "Emit the extracted structured result.",
                    "input_schema": response_model.model_json_schema(),
                }
            ],
            tool_choice={"type": "tool", "name": _STRUCTURED_OUTPUT_TOOL},
        )
        for block in response.content:
            if block.type == "tool_use" and block.name == _STRUCTURED_OUTPUT_TOOL:
                return response_model.model_validate(block.input)
        raise LLMResponseError("Model did not emit the expected structured tool call.")

    async def stream(self, *, system: str, messages: list[Message]) -> AsyncIterator[str]:
        payload: list[MessageParam] = [{"role": m.role, "content": m.content} for m in messages]
        async with self._client.messages.stream(
            model=self._model, system=system, max_tokens=_MAX_TOKENS, messages=payload
        ) as stream:
            async for text in stream.text_stream:
                yield text
