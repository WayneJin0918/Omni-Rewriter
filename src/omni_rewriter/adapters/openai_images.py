"""OpenAI-compatible ``/v1/images/generations`` client."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal

import httpx
from pydantic import Field, SecretStr

from ..models import RewriteRequest
from ..models.common import IMAGE_TASKS, StrictModel
from .base import (
    GenerationConfigurationError,
    GenerationResponseError,
    bearer_headers,
    bounded_download,
    decode_base64_media,
    request_json,
    v1_url,
)

_EXTRA_FIELDS = frozenset(
    {
        "background",
        "moderation",
        "output_compression",
        "output_format",
        "quality",
        "seed",
        "style",
        "user",
    }
)


class OpenAIImagesClientConfig(StrictModel):
    """Configuration for SGLang/OpenAI-compatible image generation."""

    base_url: str = Field(default="http://127.0.0.1:30010/v1", min_length=1)
    api_key: SecretStr | None = None
    model: str = Field(default="Qwen/Qwen-Image-2512", min_length=1)
    timeout: float = Field(default=300.0, gt=0)
    max_download_bytes: int = Field(default=64 * 1024**2, gt=0)
    response_format: Literal["b64_json", "url"] = "b64_json"


class OpenAIImagesClient:
    """Generate bounded image bytes from b64 or URL response items."""

    def __init__(
        self,
        config: OpenAIImagesClientConfig,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self._client = client
        self._owns_client = client is None

    async def __aenter__(self) -> "OpenAIImagesClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    def build_payload(
        self,
        request: RewriteRequest,
        prompt: str,
        *,
        size: str | None = None,
        n: int = 1,
        response_format: Literal["b64_json", "url"] | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if request.resolved_task not in IMAGE_TASKS:
            raise GenerationConfigurationError("OpenAI images requires an image RewriteRequest")
        if not prompt.strip():
            raise GenerationConfigurationError("image generation prompt must not be empty")
        if not 1 <= n <= 10:
            raise GenerationConfigurationError("image generation n must be from 1 through 10")
        payload: dict[str, Any] = {
            "model": self.config.model,
            "prompt": prompt,
            "n": n,
            "response_format": response_format or self.config.response_format,
        }
        resolved_size = size or request.metadata.get("size")
        if resolved_size:
            payload["size"] = resolved_size
        if extra:
            unsupported = set(extra) - _EXTRA_FIELDS
            if unsupported:
                raise GenerationConfigurationError(
                    f"unsupported OpenAI image fields: {sorted(unsupported)}"
                )
            payload.update(extra)
        return payload

    async def generate(
        self,
        request: RewriteRequest,
        prompt: str,
        *,
        size: str | None = None,
        response_format: Literal["b64_json", "url"] | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> bytes:
        """Generate exactly one image."""

        images = await self.generate_many(
            request,
            prompt,
            size=size,
            n=1,
            response_format=response_format,
            extra=extra,
        )
        return images[0]

    async def generate_many(
        self,
        request: RewriteRequest,
        prompt: str,
        *,
        size: str | None = None,
        n: int = 1,
        response_format: Literal["b64_json", "url"] | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> list[bytes]:
        """Generate one or more images, preserving server order."""

        url = v1_url(self.config.base_url, "/images/generations")
        data = await request_json(
            self._get_client(),
            "POST",
            url,
            service="OpenAI images",
            headers=self._headers(),
            json=self.build_payload(
                request,
                prompt,
                size=size,
                n=n,
                response_format=response_format,
                extra=extra,
            ),
        )
        items = data.get("data")
        if not isinstance(items, list) or not items:
            raise GenerationResponseError("OpenAI images response omitted image data")
        if len(items) != n:
            raise GenerationResponseError(
                f"OpenAI images returned {len(items)} images when {n} were requested"
            )
        return [await self._decode_item(item) for item in items]

    async def _decode_item(self, item: Any) -> bytes:
        if not isinstance(item, Mapping):
            raise GenerationResponseError("OpenAI images returned an invalid image item")
        encoded = item.get("b64_json") or item.get("b64")
        if isinstance(encoded, str) and encoded:
            return decode_base64_media(
                encoded,
                max_bytes=self.config.max_download_bytes,
                service="OpenAI images",
            )
        url = item.get("url")
        if isinstance(url, str) and url:
            return await bounded_download(
                self._get_client(),
                url,
                max_bytes=self.config.max_download_bytes,
                service="OpenAI images",
                headers=self._headers(),
                authenticated_origin=self.config.base_url,
            )
        raise GenerationResponseError("OpenAI images item omitted b64_json and url")

    def _headers(self) -> dict[str, str]:
        secret = (
            self.config.api_key.get_secret_value() if self.config.api_key is not None else None
        )
        return bearer_headers(secret)

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.config.timeout)
        return self._client
