import json
from collections.abc import AsyncIterator
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel

from careervector.config import get_settings
from careervector.core.exceptions import LLMResponseError
from careervector.infra.llm.client import Message

T = TypeVar("T", bound=BaseModel)

_STRUCTURED_OUTPUT_TOOL = "emit_result"


class DeepSeekLLMProvider:
    """Default LLMProvider, backed by DeepSeek's OpenAI-compatible chat completions API.

    Called via httpx directly rather than an OpenAI-SDK dependency, since httpx is
    already a project dependency and DeepSeek's REST surface is small (one endpoint).
    Structured output uses forced function-calling (tool_choice pinned to a single
    function matching the response_model's JSON schema) — the OpenAI-compatible
    equivalent of the forced tool-use pattern AnthropicLLMProvider uses, so
    response_model handling behaves the same across providers despite the different
    wire formats.
    """

    def __init__(self, model: str | None = None) -> None:
        settings = get_settings()
        self._model = model or settings.deepseek_default_model
        self._client = httpx.AsyncClient(
            base_url=settings.deepseek_base_url,
            headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
            timeout=60.0,
        )

    def _payload(self, system: str, messages: list[Message]) -> list[dict[str, str]]:
        return [{"role": "system", "content": system}] + [
            {"role": m.role, "content": m.content} for m in messages
        ]

    async def complete(
        self, *, system: str, messages: list[Message], response_model: type[T] | None = None
    ) -> T | str:
        body: dict[str, Any] = {
            "model": self._model,
            "messages": self._payload(system, messages),
        }
        if response_model is not None:
            body["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": _STRUCTURED_OUTPUT_TOOL,
                        "description": "Emit the extracted structured result.",
                        "parameters": response_model.model_json_schema(),
                    },
                }
            ]
            body["tool_choice"] = {
                "type": "function",
                "function": {"name": _STRUCTURED_OUTPUT_TOOL},
            }

        response = await self._client.post("/chat/completions", json=body)
        response.raise_for_status()
        message: dict[str, Any] = response.json()["choices"][0]["message"]

        if response_model is None:
            return str(message["content"])

        for call in message.get("tool_calls") or []:
            if call["function"]["name"] == _STRUCTURED_OUTPUT_TOOL:
                arguments = json.loads(call["function"]["arguments"])
                return response_model.model_validate(arguments)
        raise LLMResponseError("Model did not emit the expected structured tool call.")

    async def stream(self, *, system: str, messages: list[Message]) -> AsyncIterator[str]:
        body = {"model": self._model, "messages": self._payload(system, messages), "stream": True}
        async with self._client.stream("POST", "/chat/completions", json=body) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                data = line.removeprefix("data: ") if line.startswith("data: ") else None
                if data is None or data == "[DONE]":
                    continue
                delta: dict[str, Any] = json.loads(data)["choices"][0]["delta"]
                if content := delta.get("content"):
                    yield str(content)
