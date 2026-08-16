import json

import httpx
import pytest
from pydantic import BaseModel

from careervector.core.exceptions import LLMResponseError
from careervector.infra.llm.client import Message
from careervector.infra.llm.deepseek_provider import DeepSeekLLMProvider

pytestmark = pytest.mark.unit


class _Extracted(BaseModel):
    value: str


def _provider(handler: httpx.MockTransport) -> DeepSeekLLMProvider:
    provider = DeepSeekLLMProvider(model="deepseek-chat")
    provider._client = httpx.AsyncClient(transport=handler, base_url="https://api.deepseek.com")
    return provider


async def test_complete_without_response_model_returns_message_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "hello there"}}]},
        )

    provider = _provider(httpx.MockTransport(handler))
    result = await provider.complete(system="sys", messages=[Message(role="user", content="hi")])

    assert result == "hello there"


async def test_complete_with_response_model_parses_forced_tool_call() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["tool_choice"] == {"type": "function", "function": {"name": "emit_result"}}
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "function": {
                                        "name": "emit_result",
                                        "arguments": json.dumps({"value": "parsed"}),
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
        )

    provider = _provider(httpx.MockTransport(handler))
    result = await provider.complete(
        system="sys", messages=[Message(role="user", content="hi")], response_model=_Extracted
    )

    assert result == _Extracted(value="parsed")


async def test_complete_with_response_model_raises_when_no_tool_call_emitted() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": "no tool call"}}]})

    provider = _provider(httpx.MockTransport(handler))

    with pytest.raises(LLMResponseError):
        await provider.complete(
            system="sys", messages=[Message(role="user", content="hi")], response_model=_Extracted
        )


async def test_stream_yields_delta_content_chunks() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        chunks = [
            {"choices": [{"delta": {"content": "Hel"}}]},
            {"choices": [{"delta": {"content": "lo"}}]},
        ]
        body = "".join(f"data: {json.dumps(c)}\n\n" for c in chunks) + "data: [DONE]\n\n"
        return httpx.Response(200, content=body)

    provider = _provider(httpx.MockTransport(handler))
    chunks = [
        c
        async for c in provider.stream(system="sys", messages=[Message(role="user", content="hi")])
    ]

    assert "".join(chunks) == "Hello"
