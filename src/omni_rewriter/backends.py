"""Async OpenAI-compatible chat backends without an OpenAI SDK dependency."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from typing import Any, Protocol, runtime_checkable

import httpx
from pydantic import BaseModel, Field, SecretStr

from .errors import (
    BackendConfigurationError,
    BackendResponseError,
    BackendTransportError,
)
from .models.common import StrictModel

ChatMessage = Mapping[str, Any]


def _guidance_safe_schema(value: Any) -> Any:
    """Remove validation-only regexes unsupported by common grammar backends.

    Pydantic emits a negative-lookahead pattern for ``Decimal`` fields. vLLM's
    structured-output grammar rejects look-around before generation starts;
    Omni-Rewriter still applies the complete Pydantic validation after decoding.
    """

    if isinstance(value, Mapping):
        return {key: _guidance_safe_schema(item) for key, item in value.items() if key != "pattern"}
    if isinstance(value, list):
        return [_guidance_safe_schema(item) for item in value]
    return value


class ChatBackendConfig(StrictModel):
    """Configuration shared by OpenAI-compatible chat-completions servers."""

    base_url: str = Field(min_length=1)
    api_key: SecretStr | None = None
    model: str = Field(min_length=1)
    timeout: float = Field(default=60.0, gt=0)
    retries: int = Field(default=2, ge=0, le=10)
    temperature: float | None = Field(default=0.2, ge=0, le=2)
    max_tokens: int | None = Field(default=None, gt=0)
    enable_thinking: bool | None = None


@runtime_checkable
class ChatBackend(Protocol):
    """Transport-neutral asynchronous chat-completion backend."""

    async def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        response_model: type[BaseModel] | None = None,
    ) -> str:
        """Return the assistant's textual response."""


class OpenAICompatibleBackend:
    """Small httpx client for the OpenAI chat-completions wire format."""

    def __init__(
        self,
        config: ChatBackendConfig,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self._client = client
        self._owns_client = client is None

    async def __aenter__(self) -> "OpenAICompatibleBackend":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    async def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        response_model: type[BaseModel] | None = None,
    ) -> str:
        if not messages:
            raise BackendConfigurationError("at least one chat message is required")
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": list(messages),
        }
        if self.config.temperature is not None:
            payload["temperature"] = self.config.temperature
        if self.config.max_tokens is not None:
            payload["max_tokens"] = self.config.max_tokens
        if self.config.enable_thinking is not None:
            # vLLM forwards model-specific switches through the chat template.
            payload["chat_template_kwargs"] = {"enable_thinking": self.config.enable_thinking}
        if response_model is not None:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "strict": True,
                    "schema": _guidance_safe_schema(response_model.model_json_schema()),
                },
            }

        headers = {"Content-Type": "application/json"}
        if self.config.api_key is not None:
            headers["Authorization"] = f"Bearer {self.config.api_key.get_secret_value()}"

        client = self._get_client()
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        for attempt in range(self.config.retries + 1):
            try:
                response = await client.post(url, headers=headers, json=payload)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                if attempt >= self.config.retries:
                    raise BackendTransportError(
                        f"chat request failed after {attempt + 1} attempts: {type(exc).__name__}"
                    ) from exc
                await asyncio.sleep(min(0.25 * (2**attempt), 2.0))
                continue

            if response.status_code in {408, 409, 429} or response.status_code >= 500:
                if attempt < self.config.retries:
                    await asyncio.sleep(min(0.25 * (2**attempt), 2.0))
                    continue
            if response.is_error:
                raise BackendResponseError(f"chat backend returned HTTP {response.status_code}")
            return self._extract_content(response)
        raise BackendTransportError("chat request retry loop terminated unexpectedly")

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.config.timeout)
        return self._client

    @staticmethod
    def _extract_content(response: httpx.Response) -> str:
        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise BackendResponseError("chat backend returned a malformed response") from exc
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text = "".join(
                str(part.get("text", ""))
                for part in content
                if isinstance(part, Mapping) and part.get("type") == "text"
            )
            if text:
                return text
        raise BackendResponseError("chat backend response has no textual content")


class FakeBackend:
    """Simple fixed-response backend for examples and smoke tests."""

    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[list[ChatMessage]] = []

    async def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        response_model: type[BaseModel] | None = None,
    ) -> str:
        del response_model
        self.calls.append(list(messages))
        return self.response


class ScriptedBackend:
    """FIFO backend that makes multi-step agent behavior deterministic."""

    def __init__(self, responses: Sequence[str | Exception]) -> None:
        self._responses = list(responses)
        self.calls: list[list[ChatMessage]] = []

    async def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        response_model: type[BaseModel] | None = None,
    ) -> str:
        del response_model
        self.calls.append(list(messages))
        if not self._responses:
            raise BackendResponseError("scripted backend has no response remaining")
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    async def aclose(self) -> None:
        """No-op so ScriptedBackend can stand in for OpenAICompatibleBackend in tests."""
