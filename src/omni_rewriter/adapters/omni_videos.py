"""OpenAI-style video jobs for vLLM-Omni and SGLang Omni services."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

import httpx
from pydantic import Field, SecretStr

from ..models import MediaRole, MediaType, RewriteRequest
from ..models.common import VIDEO_TASKS, StrictModel
from .base import (
    GenerationConfigurationError,
    GenerationResponseError,
    bearer_headers,
    bounded_download,
    bounded_download_to_path,
    decode_base64_media,
    first_value,
    request_json,
    v1_url,
    wait_for_terminal,
)

_SIZE_RE = re.compile(r"^[1-9][0-9]{0,4}x[1-9][0-9]{0,4}$")
_WAN_EXTRA_FIELDS = frozenset(
    {
        "fps",
        "frames_per_second",
        "guidance_scale",
        "negative_prompt",
        "num_frames",
        "num_inference_steps",
        "output_format",
        "watermark",
    }
)


class OmniVideosClientConfig(StrictModel):
    """Transport and safety limits for an OpenAI-style videos endpoint."""

    base_url: str = Field(default="http://127.0.0.1:8091/v1", min_length=1)
    api_key: SecretStr | None = None
    timeout: float = Field(default=60.0, gt=0)
    poll_interval: float = Field(default=2.0, gt=0)
    poll_timeout: float = Field(default=900.0, gt=0)
    max_download_bytes: int = Field(default=2 * 1024**3, gt=0)
    max_reference_bytes: int = Field(default=32 * 1024**2, gt=0)
    transport: Literal["json", "multipart"] = "multipart"


class WanOmniAdapter(StrictModel):
    """Deterministic WAN request-to-Omni payload mapper."""

    model: str = Field(default="Wan-AI/Wan2.2-T2V-A14B", min_length=1)
    default_size: str = Field(default="832x480", pattern=_SIZE_RE.pattern)
    min_seconds: int = Field(default=1, gt=0)
    max_seconds: int = Field(default=20, gt=0)

    def build_payload(
        self,
        request: RewriteRequest,
        prompt: str,
        *,
        extra: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if request.resolved_task not in VIDEO_TASKS:
            raise GenerationConfigurationError("WAN generation requires a video RewriteRequest")
        if not prompt.strip():
            raise GenerationConfigurationError("WAN generation prompt must not be empty")
        duration = int(request.duration_seconds or 0)
        if request.duration_seconds != duration or not self.min_seconds <= duration <= self.max_seconds:
            raise GenerationConfigurationError(
                f"WAN duration must be an integer from {self.min_seconds} through {self.max_seconds}"
            )
        size = request.metadata.get("size")
        if not size:
            width = request.metadata.get("width")
            height = request.metadata.get("height")
            size = f"{width}x{height}" if width and height else self.default_size
        if not _SIZE_RE.fullmatch(size):
            raise GenerationConfigurationError("WAN size must use WIDTHxHEIGHT positive integers")

        payload: dict[str, Any] = {
            "model": request.metadata.get("model", self.model),
            "prompt": prompt,
            "size": size,
            "seconds": duration,
        }
        seed = request.metadata.get("seed")
        if seed is not None:
            payload["seed"] = _parse_int(seed, "seed")

        references: list[str] = []
        for media in request.media:
            if media.media_type is not MediaType.IMAGE:
                raise GenerationConfigurationError("WAN Omni accepts only image references")
            if media.role is MediaRole.FIRST_FRAME:
                payload["input_reference"] = media.uri
            elif media.role is MediaRole.LAST_FRAME:
                payload["last_frame"] = media.uri
            else:
                references.append(media.uri)
        if references:
            payload["reference_images"] = references

        if extra:
            unsupported = set(extra) - _WAN_EXTRA_FIELDS
            if unsupported:
                raise GenerationConfigurationError(
                    f"unsupported WAN Omni fields: {sorted(unsupported)}"
                )
            payload.update(extra)
        return payload


class OmniVideosClient:
    """Submit, poll, and fetch OpenAI-style asynchronous video jobs."""

    def __init__(
        self,
        config: OmniVideosClientConfig,
        *,
        mapper: WanOmniAdapter | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self.mapper = mapper or WanOmniAdapter()
        self._client = client
        self._owns_client = client is None

    async def __aenter__(self) -> "OmniVideosClient":
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
        extra: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.mapper.build_payload(request, prompt, extra=extra)

    async def submit(
        self,
        request: RewriteRequest,
        prompt: str,
        *,
        extra: Mapping[str, Any] | None = None,
    ) -> str:
        """Submit exactly once; callers must provide their own idempotency strategy."""

        payload = self.build_payload(request, prompt, extra=extra)
        kwargs: dict[str, Any]
        if self.config.transport == "json":
            kwargs = {"json": payload}
        else:
            kwargs = {"files": self._multipart(payload)}
        data = await request_json(
            self._get_client(),
            "POST",
            v1_url(self.config.base_url, "/videos"),
            service="Omni videos",
            headers=self._headers(),
            **kwargs,
        )
        task_id = first_value(data, "id", "task_id", "video_id")
        if not task_id:
            raise GenerationResponseError("Omni videos submit response omitted a task id")
        return str(task_id)

    async def query(self, task_id: str) -> dict[str, Any]:
        if not task_id:
            raise GenerationConfigurationError("video task id must not be empty")
        return await request_json(
            self._get_client(),
            "GET",
            v1_url(self.config.base_url, f"/videos/{task_id}"),
            service="Omni videos",
            headers=self._headers(),
        )

    async def wait(self, task_id: str) -> dict[str, Any]:
        return await wait_for_terminal(
            task_id,
            self.query,
            service="Omni videos",
            poll_interval=self.config.poll_interval,
            poll_timeout=self.config.poll_timeout,
        )

    async def poll(self, task_id: str) -> dict[str, Any]:
        return await self.wait(task_id)

    async def download_bytes(
        self,
        task_id: str,
        *,
        result: Mapping[str, Any] | None = None,
    ) -> bytes:
        data = dict(result) if result is not None else await self.wait(task_id)
        url = _download_url(data) or v1_url(
            self.config.base_url, f"/videos/{task_id}/content"
        )
        return await bounded_download(
            self._get_client(),
            url,
            max_bytes=self.config.max_download_bytes,
            service="Omni videos",
            headers=self._headers(),
            authenticated_origin=self.config.base_url,
        )

    async def download(
        self,
        task_id: str,
        destination: str | Path,
        *,
        result: Mapping[str, Any] | None = None,
    ) -> Path:
        data = dict(result) if result is not None else await self.wait(task_id)
        url = _download_url(data) or v1_url(
            self.config.base_url, f"/videos/{task_id}/content"
        )
        return await bounded_download_to_path(
            self._get_client(),
            url,
            destination,
            max_bytes=self.config.max_download_bytes,
            service="Omni videos",
            headers=self._headers(),
            authenticated_origin=self.config.base_url,
        )

    def _multipart(self, payload: Mapping[str, Any]) -> list[tuple[str, tuple[Any, ...]]]:
        parts: list[tuple[str, tuple[Any, ...]]] = []
        for key, value in payload.items():
            values = value if isinstance(value, list) else [value]
            for item in values:
                if key in {"input_reference", "last_frame", "reference_images"}:
                    parts.append((key, self._reference_part(str(item), key)))
                else:
                    encoded = json.dumps(item) if isinstance(item, (dict, list)) else str(item)
                    parts.append((key, (None, encoded)))
        return parts

    def _reference_part(self, uri: str, field: str) -> tuple[Any, ...]:
        if not uri.startswith("data:"):
            return (None, uri)
        header, separator, encoded = uri.partition(",")
        if not separator or ";base64" not in header:
            raise GenerationConfigurationError(
                "multipart data references must be base64 data URIs"
            )
        mime_type = header[5:].split(";", 1)[0] or "application/octet-stream"
        content = decode_base64_media(
            encoded,
            max_bytes=self.config.max_reference_bytes,
            service="Omni videos reference",
        )
        extension = mime_type.split("/", 1)[-1].split("+", 1)[0]
        return (f"{field}.{extension}", content, mime_type)

    def _headers(self) -> dict[str, str]:
        secret = (
            self.config.api_key.get_secret_value() if self.config.api_key is not None else None
        )
        return bearer_headers(secret)

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.config.timeout)
        return self._client


def _download_url(data: Mapping[str, Any]) -> str | None:
    value = first_value(data, "download_url", "video_url", "url")
    return value if isinstance(value, str) and value else None


def _parse_int(value: str, name: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise GenerationConfigurationError(f"WAN metadata {name!r} must be an integer") from exc
