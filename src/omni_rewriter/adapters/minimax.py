"""Async MiniMax H3 API adapter."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Mapping
from typing import Any

import httpx
from pydantic import Field, SecretStr

from ..errors import BackendConfigurationError, BackendResponseError, BackendTransportError
from ..models import MediaReference, MediaRole, MediaType, RewriteRequest, TaskType
from ..models.common import StrictModel

_ENDPOINTS = {
    "h3_context_ir": "/v2/h3_context_ir",
    "video_generation": "/v2/video_generation",
    "video_regeneration": "/v2/video_regeneration",
}
_PENDING = {
    "pending",
    "queued",
    "queueing",
    "preparing",
    "processing",
    "running",
    "in_progress",
}
_SUCCEEDED = {"success", "succeeded", "completed", "done"}
_FAILED = {"fail", "failed", "error", "cancelled", "canceled", "expired", "rejected"}


class MiniMaxClientConfig(StrictModel):
    """Global defaults; set base_url to https://api.minimaxi.com for mainland China."""

    api_key: SecretStr
    base_url: str = Field(default="https://api.minimax.io", min_length=1)
    timeout: float = Field(default=60.0, gt=0)
    poll_interval: float = Field(default=2.0, gt=0)
    poll_timeout: float = Field(default=900.0, gt=0)


class MiniMaxClient:
    def __init__(
        self,
        config: MiniMaxClientConfig,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self._client = client
        self._owns_client = client is None

    async def __aenter__(self) -> "MiniMaxClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    @staticmethod
    def content_item(media: MediaReference, *, regeneration: bool = False) -> dict[str, Any]:
        kind = f"{media.media_type.value}_url"
        if regeneration and media.role is MediaRole.SOURCE:
            if media.media_type is not MediaType.VIDEO:
                raise BackendConfigurationError("MiniMax base_video must be video media")
            role = "base_video"
        elif media.role in {MediaRole.FIRST_FRAME, MediaRole.LAST_FRAME}:
            role = media.role.value
        else:
            role = f"reference_{media.media_type.value}"
        return {"type": kind, kind: {"url": media.uri}, "role": role}

    @classmethod
    def build_context_payload(cls, request: RewriteRequest) -> dict[str, Any]:
        """Map all rewrite media to MiniMax condition objects."""

        requested_duration = request.duration_seconds
        if requested_duration is None:
            raise BackendConfigurationError("MiniMax H3 requires a video RewriteRequest")
        duration = int(requested_duration)
        if requested_duration != duration or not 4 <= duration <= 15:
            raise BackendConfigurationError(
                "MiniMax H3 duration must be an integer from 4 through 15"
            )
        ratio = request.metadata.get(
            "ratio",
            "16:9" if request.resolved_task is TaskType.T2VA else "adaptive",
        )
        return {
            "model": request.metadata.get("model", "MiniMax-H3"),
            "content": [
                {"type": "text", "text": request.prompt},
                *(cls.content_item(item) for item in request.media),
            ],
            "duration": duration,
            "ratio": ratio,
        }

    @classmethod
    def build_regeneration_payload(cls, request: RewriteRequest) -> dict[str, Any]:
        if (
            sum(
                item.role is MediaRole.SOURCE and item.media_type is MediaType.VIDEO
                for item in request.media
            )
            != 1
        ):
            raise BackendConfigurationError(
                "MiniMax regeneration requires exactly one source video"
            )
        resolution = request.metadata.get("resolution", "2K")
        if resolution not in {"768P", "1080P", "2K"}:
            raise BackendConfigurationError(
                "MiniMax regeneration resolution must be 768P, 1080P, or 2K"
            )
        return {
            "model": request.metadata.get("model", "MiniMax-H3"),
            "content": [
                {"type": "text", "text": request.prompt},
                *(cls.content_item(item, regeneration=True) for item in request.media),
            ],
            "resolution": resolution,
        }

    async def submit_h3_context_ir(self, request: RewriteRequest | Mapping[str, Any]) -> str:
        payload = (
            self.build_context_payload(request)
            if isinstance(request, RewriteRequest)
            else dict(request)
        )
        return await self.submit("h3_context_ir", payload)

    async def submit_video_generation(self, payload: Mapping[str, Any]) -> str:
        return await self.submit("video_generation", payload)

    async def submit_video_regeneration(self, payload: RewriteRequest | Mapping[str, Any]) -> str:
        body = (
            self.build_regeneration_payload(payload)
            if isinstance(payload, RewriteRequest)
            else dict(payload)
        )
        return await self.submit("video_regeneration", body)

    async def submit(self, endpoint: str, payload: Mapping[str, Any]) -> str:
        data = await self._request("POST", self._path(endpoint), json=dict(payload))
        task_id = _first(data, "task_id", "id", "video_id")
        if not task_id:
            raise BackendResponseError(f"MiniMax {endpoint} response omitted a task id")
        return str(task_id)

    async def query(self, task_id: str) -> dict[str, Any]:
        return await self._request(
            "GET",
            f"/v2/query/video_generation/{task_id}",
        )

    async def wait(self, task_id: str) -> dict[str, Any]:
        deadline = time.monotonic() + self.config.poll_timeout
        while True:
            data = await self.query(task_id)
            status = str(_first(data, "status", "state") or "").lower()
            if status in _SUCCEEDED:
                return data
            if status in _FAILED:
                detail = _first(data, "error", "message", "detail") or "no failure detail"
                raise BackendResponseError(f"MiniMax task {task_id} failed: {detail}")
            if status not in _PENDING:
                raise BackendResponseError(
                    f"MiniMax task {task_id} returned unknown status {status!r}"
                )
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise BackendTransportError(f"MiniMax task {task_id} timed out")
            await asyncio.sleep(min(self.config.poll_interval, remaining))

    async def poll(self, task_id: str) -> dict[str, Any]:
        """Poll any of the three task types through the shared query endpoint."""

        return await self.wait(task_id)

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self.config.base_url.rstrip('/')}{path}"
        try:
            response = await self._get_client().request(
                method,
                url,
                headers={
                    "Authorization": f"Bearer {self.config.api_key.get_secret_value()}",
                    "Content-Type": "application/json",
                },
                **kwargs,
            )
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise BackendTransportError(f"MiniMax request failed: {type(exc).__name__}") from exc
        if response.is_error:
            raise BackendResponseError(f"MiniMax returned HTTP {response.status_code}")
        try:
            data = response.json()
        except ValueError as exc:
            raise BackendResponseError("MiniMax returned a non-JSON response") from exc
        if not isinstance(data, dict):
            raise BackendResponseError("MiniMax returned a non-object response")
        base_response = data.get("base_resp") or data.get("base_response")
        if isinstance(base_response, Mapping):
            code = base_response.get("status_code", base_response.get("code", 0))
            if code not in (0, "0", None):
                message = base_response.get("status_msg") or base_response.get("message")
                raise BackendResponseError(f"MiniMax API error {code}: {message or 'unknown'}")
        return data

    @staticmethod
    def _path(endpoint: str) -> str:
        try:
            return _ENDPOINTS[endpoint]
        except KeyError as exc:
            raise BackendConfigurationError(f"unsupported MiniMax endpoint {endpoint!r}") from exc

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.config.timeout)
        return self._client


def _first(data: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    for nested_key in ("data", "task"):
        nested = data.get(nested_key)
        if isinstance(nested, Mapping):
            value = _first(nested, *keys)
            if value is not None:
                return value
    return None
