from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from omni_rewriter.backends import ChatBackendConfig, OpenAICompatibleBackend
from omni_rewriter.errors import (
    BackendConfigurationError,
    BackendResponseError,
    BackendTransportError,
)
from omni_rewriter.models import BaseRewrite


@pytest.mark.asyncio
async def test_backend_payload_and_schema() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        assert request.headers["authorization"] == "Bearer secret"
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    backend = OpenAICompatibleBackend(
        ChatBackendConfig(
            base_url="http://writer.test/v1",
            api_key="secret",
            model="qwen",
            max_tokens=200,
            enable_thinking=False,
        ),
        client=client,
    )
    assert (
        await backend.complete([{"role": "user", "content": "hi"}], response_model=BaseRewrite)
        == "{}"
    )
    assert captured["model"] == "qwen"
    assert captured["max_tokens"] == 200
    assert captured["chat_template_kwargs"] == {"enable_thinking": False}
    assert captured["response_format"]["json_schema"]["strict"] is True
    schema_text = json.dumps(captured["response_format"]["json_schema"]["schema"])
    assert '"pattern"' not in schema_text
    await client.aclose()


@pytest.mark.asyncio
async def test_backend_retries_status(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(429)
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    async def no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr("omni_rewriter.backends.asyncio.sleep", no_sleep)
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    backend = OpenAICompatibleBackend(
        ChatBackendConfig(base_url="http://writer.test/v1", model="qwen", retries=1),
        client=client,
    )
    assert await backend.complete([{"role": "user", "content": "hi"}]) == "ok"
    assert attempts == 2
    await client.aclose()


@pytest.mark.asyncio
async def test_backend_transport_exhaustion(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    async def no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr("omni_rewriter.backends.asyncio.sleep", no_sleep)
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    backend = OpenAICompatibleBackend(
        ChatBackendConfig(base_url="http://writer.test/v1", model="qwen", retries=1),
        client=client,
    )
    with pytest.raises(BackendTransportError, match="2 attempts"):
        await backend.complete([{"role": "user", "content": "hi"}])
    await client.aclose()


@pytest.mark.asyncio
async def test_backend_errors() -> None:
    async def run(response: httpx.Response) -> None:
        client = httpx.AsyncClient(transport=httpx.MockTransport(lambda _: response))
        backend = OpenAICompatibleBackend(
            ChatBackendConfig(base_url="http://writer.test/v1", model="qwen", retries=0),
            client=client,
        )
        with pytest.raises(BackendResponseError):
            await backend.complete([{"role": "user", "content": "hi"}])
        await client.aclose()

    await run(httpx.Response(400))
    await run(httpx.Response(200, json={"choices": []}))
    await run(httpx.Response(200, json={"choices": [{"message": {"content": None}}]}))


@pytest.mark.asyncio
async def test_backend_extracts_text_parts() -> None:
    response = httpx.Response(
        200,
        json={
            "choices": [
                {
                    "message": {
                        "content": [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]
                    }
                }
            ]
        },
    )
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda _: response))
    backend = OpenAICompatibleBackend(
        ChatBackendConfig(base_url="http://writer.test/v1", model="qwen"),
        client=client,
    )
    assert await backend.complete([{"role": "user", "content": "hi"}]) == "ab"
    await client.aclose()


@pytest.mark.asyncio
async def test_backend_requires_messages() -> None:
    backend = OpenAICompatibleBackend(
        ChatBackendConfig(base_url="http://writer.test/v1", model="qwen")
    )
    with pytest.raises(BackendConfigurationError):
        await backend.complete([])
