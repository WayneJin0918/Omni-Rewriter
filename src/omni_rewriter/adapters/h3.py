"""Async adapter for a local H3 SGLang ``/v1/videos`` service."""

from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from typing import Any, Mapping

import httpx
from pydantic import Field, SecretStr

from ..errors import BackendConfigurationError, BackendResponseError, BackendTransportError
from ..models import MediaReference, MediaRole, RewriteRequest, TaskType
from ..models.common import StrictModel

_PENDING = {"pending", "queued", "submitted", "processing", "running", "in_progress"}
_SUCCEEDED = {"completed", "succeeded", "success", "done"}
_FAILED = {"failed", "error", "cancelled", "canceled", "rejected", "expired"}


class H3ClientConfig(StrictModel):
    base_url: str = Field(min_length=1)
    api_key: SecretStr | None = None
    timeout: float = Field(default=60.0, gt=0)
    poll_interval: float = Field(default=2.0, gt=0)
    poll_timeout: float = Field(default=900.0, gt=0)
    max_download_bytes: int = Field(default=2 * 1024**3, gt=0)


class H3Client:
    """Submit, poll and download local H3 video jobs."""

    def __init__(
        self,
        config: H3ClientConfig,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self._client = client
        self._owns_client = client is None

    async def __aenter__(self) -> "H3Client":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    @staticmethod
    def condition(media: MediaReference) -> dict[str, Any]:
        """Map a transport-neutral media reference without losing its role."""

        condition: dict[str, Any] = {
            "type": media.media_type.value,
            "uri": media.uri,
        }
        if media.role is MediaRole.FIRST_FRAME:
            condition.update(role="keyframe", frame_index=0)
        elif media.role is MediaRole.LAST_FRAME:
            condition.update(role="keyframe", frame_index=-1)
        else:
            condition["role"] = "reference"
        return condition

    def build_payload(
        self,
        request: RewriteRequest,
        prompt: str,
        *,
        model: str | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        duration = int(request.duration_seconds)
        if request.duration_seconds != duration or not 4 <= duration <= 15:
            raise BackendConfigurationError(
                "H3 duration must be an integer from 4 through 15 seconds"
            )
        task = request.resolved_task
        server_task = (
            TaskType.FL2VA.value
            if task in {TaskType.I2VA, TaskType.L2VA, TaskType.FL2VA}
            else task.value
        )
        aspect_ratio = request.metadata.get("aspect_ratio", "auto" if request.media else "16:9")
        payload: dict[str, Any] = {
            "task": server_task,
            "prompt": prompt,
            "conditions": [self.condition(item) for item in request.media],
            "target": {
                "short_edge": int(request.metadata.get("short_edge", "768")),
                "aspect_ratio": aspect_ratio,
                "duration_seconds": duration,
            },
            "seed": int(request.metadata.get("seed", "0")),
        }
        if extra:
            unsupported = set(extra) - {"task", "prompt", "conditions", "target", "seed"}
            if unsupported:
                raise BackendConfigurationError(
                    f"unsupported H3 payload fields: {sorted(unsupported)}"
                )
            payload.update(extra)
        # Kept for source compatibility; the local H3 endpoint does not document a model field.
        del model
        return payload

    async def submit(
        self,
        request: RewriteRequest,
        prompt: str,
        *,
        model: str | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> str:
        data = await self._request(
            "POST",
            "/v1/videos",
            json=self.build_payload(request, prompt, model=model, extra=extra),
        )
        task_id = _first(data, "id", "task_id", "video_id")
        if not task_id:
            raise BackendResponseError("H3 submit response omitted a video task id")
        return str(task_id)

    async def query(self, task_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/v1/videos/{task_id}")

    async def wait(self, task_id: str) -> dict[str, Any]:
        deadline = time.monotonic() + self.config.poll_timeout
        while True:
            result = await self.query(task_id)
            status = str(_first(result, "status", "state") or "").lower()
            if status in _SUCCEEDED:
                return result
            if status in _FAILED:
                detail = _first(result, "error", "message", "detail") or "no failure detail"
                raise BackendResponseError(f"H3 task {task_id} failed: {detail}")
            if status not in _PENDING:
                raise BackendResponseError(f"H3 task {task_id} returned unknown status {status!r}")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise BackendTransportError(f"H3 task {task_id} timed out")
            await asyncio.sleep(min(self.config.poll_interval, remaining))

    async def poll(self, task_id: str) -> dict[str, Any]:
        """Poll until the task reaches a terminal state."""

        return await self.wait(task_id)

    async def download(
        self,
        task_id: str,
        destination: str | Path,
        *,
        result: Mapping[str, Any] | None = None,
    ) -> Path:
        data = dict(result) if result is not None else await self.wait(task_id)
        url = _download_url(data)
        if not url:
            url = f"{self.config.base_url.rstrip('/')}/v1/videos/{task_id}/content"
        destination_path = Path(destination)
        temporary = destination_path.with_name(f".{destination_path.name}.part")
        client = self._get_client()
        try:
            async with client.stream("GET", url, headers=self._headers()) as response:
                if response.is_error:
                    raise BackendResponseError(f"H3 download returned HTTP {response.status_code}")
                length = response.headers.get("content-length")
                if length and length.isdigit() and int(length) > self.config.max_download_bytes:
                    raise BackendResponseError("H3 video exceeds the configured download limit")
                total = 0
                with temporary.open("wb") as stream:
                    async for chunk in response.aiter_bytes():
                        total += len(chunk)
                        if total > self.config.max_download_bytes:
                            raise BackendResponseError(
                                "H3 video exceeds the configured download limit"
                            )
                        stream.write(chunk)
            os.replace(temporary, destination_path)
            return destination_path
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise BackendTransportError(f"H3 download failed: {type(exc).__name__}") from exc
        finally:
            if temporary.exists():
                temporary.unlink()

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self.config.base_url.rstrip('/')}{path}"
        try:
            response = await self._get_client().request(
                method, url, headers=self._headers(), **kwargs
            )
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise BackendTransportError(f"H3 request failed: {type(exc).__name__}") from exc
        if response.is_error:
            raise BackendResponseError(f"H3 returned HTTP {response.status_code}")
        try:
            data = response.json()
        except ValueError as exc:
            raise BackendResponseError("H3 returned a non-JSON response") from exc
        if not isinstance(data, dict):
            raise BackendResponseError("H3 returned a non-object response")
        return data

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.config.api_key is not None:
            headers["Authorization"] = f"Bearer {self.config.api_key.get_secret_value()}"
        return headers

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.config.timeout)
        return self._client


def _first(data: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    nested = data.get("data")
    if isinstance(nested, Mapping):
        return _first(nested, *keys)
    return None


def _download_url(data: Mapping[str, Any]) -> str | None:
    value = _first(data, "download_url", "video_url", "url")
    if isinstance(value, str) and value:
        return value
    output = data.get("output")
    if isinstance(output, Mapping):
        value = _first(output, "download_url", "video_url", "url")
        if isinstance(value, str) and value:
            return value
    return None
