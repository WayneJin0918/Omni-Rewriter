"""Shared contracts and bounded I/O helpers for generation adapters."""

from __future__ import annotations

import asyncio
import base64
import binascii
import os
import time
from collections.abc import Awaitable, Callable, Mapping
from pathlib import Path
from typing import Any, Protocol, runtime_checkable
from urllib.parse import urlsplit

import httpx

from ..errors import OmniRewriterError
from ..models import RewriteRequest

PENDING_STATUSES = frozenset(
    {"pending", "queued", "submitted", "processing", "running", "in_progress"}
)
SUCCEEDED_STATUSES = frozenset({"completed", "succeeded", "success", "done"})
FAILED_STATUSES = frozenset(
    {"failed", "error", "cancelled", "canceled", "rejected", "expired"}
)


class GenerationAdapterError(OmniRewriterError):
    """Base error for optional online generation adapters."""


class GenerationConfigurationError(GenerationAdapterError):
    """A generation request or adapter configuration is invalid."""


class GenerationTransportError(GenerationAdapterError):
    """A generation endpoint could not be reached or timed out."""


class GenerationResponseError(GenerationAdapterError):
    """A generation endpoint returned an unsuccessful or malformed response."""


class GenerationTooLargeError(GenerationResponseError):
    """Generated media exceeded its configured byte limit."""


@runtime_checkable
class ImageGeneratorAdapter(Protocol):
    """Generate one bounded image from a validated request and rendered prompt."""

    async def generate(self, request: RewriteRequest, prompt: str) -> bytes: ...


@runtime_checkable
class VideoGeneratorAdapter(Protocol):
    """Submit, wait for, and download an asynchronous video generation."""

    async def submit(self, request: RewriteRequest, prompt: str) -> str: ...

    async def wait(self, task_id: str) -> dict[str, Any]: ...

    async def download(
        self,
        task_id: str,
        destination: str | Path,
        *,
        result: Mapping[str, Any] | None = None,
    ) -> Path: ...


def bearer_headers(api_key: str | None, *, accept: str = "application/json") -> dict[str, str]:
    """Build headers without ever stringifying a secret wrapper."""

    headers = {"Accept": accept}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def v1_url(base_url: str, path: str) -> str:
    """Join an API origin or an existing ``/v1`` base with a v1-relative path."""

    base = base_url.rstrip("/")
    suffix = path if path.startswith("/") else f"/{path}"
    return f"{base}{suffix}" if base.endswith("/v1") else f"{base}/v1{suffix}"


def first_value(data: Mapping[str, Any], *keys: str) -> Any:
    """Find a value in common response envelopes."""

    for key in keys:
        if key in data:
            return data[key]
    for nested_key in ("data", "task", "output", "result"):
        nested = data.get(nested_key)
        if isinstance(nested, Mapping):
            value = first_value(nested, *keys)
            if value is not None:
                return value
    return None


async def request_json(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    service: str,
    headers: Mapping[str, str] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Make one HTTP request and normalize transport, HTTP, and JSON errors."""

    try:
        response = await client.request(method, url, headers=headers, **kwargs)
    except (httpx.TimeoutException, httpx.TransportError) as exc:
        raise GenerationTransportError(
            f"{service} request failed: {type(exc).__name__}"
        ) from exc
    if response.is_error:
        raise GenerationResponseError(
            f"{service} returned HTTP {response.status_code}: {_error_detail(response)}"
        )
    try:
        data = response.json()
    except ValueError as exc:
        raise GenerationResponseError(f"{service} returned a non-JSON response") from exc
    if not isinstance(data, dict):
        raise GenerationResponseError(f"{service} returned a non-object response")
    return data


async def wait_for_terminal(
    task_id: str,
    query: Callable[[str], Awaitable[dict[str, Any]]],
    *,
    service: str,
    poll_interval: float,
    poll_timeout: float,
) -> dict[str, Any]:
    """Poll a task until a known terminal state or a bounded deadline."""

    deadline = time.monotonic() + poll_timeout
    while True:
        result = await query(task_id)
        status = str(first_value(result, "status", "state") or "").lower()
        if status in SUCCEEDED_STATUSES:
            return result
        if status in FAILED_STATUSES:
            detail = first_value(result, "error", "message", "detail") or "no failure detail"
            raise GenerationResponseError(f"{service} task {task_id} failed: {detail}")
        if status not in PENDING_STATUSES:
            raise GenerationResponseError(
                f"{service} task {task_id} returned unknown status {status!r}"
            )
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise GenerationTransportError(f"{service} task {task_id} timed out")
        await asyncio.sleep(min(poll_interval, remaining))


def decode_base64_media(value: str, *, max_bytes: int, service: str) -> bytes:
    """Decode base64 while bounding both estimated and actual output size."""

    encoded = value.split(",", 1)[1] if value.startswith("data:") and "," in value else value
    compact = "".join(encoded.split())
    estimated = (len(compact) * 3) // 4
    if estimated > max_bytes + 2:
        raise GenerationTooLargeError(f"{service} media exceeds the configured byte limit")
    try:
        content = base64.b64decode(compact, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise GenerationResponseError(f"{service} returned invalid base64 media") from exc
    if len(content) > max_bytes:
        raise GenerationTooLargeError(f"{service} media exceeds the configured byte limit")
    return content


async def bounded_download(
    client: httpx.AsyncClient,
    url: str,
    *,
    max_bytes: int,
    service: str,
    headers: Mapping[str, str] | None = None,
    authenticated_origin: str | None = None,
) -> bytes:
    """Download HTTP(S) bytes with a hard cap and no cross-origin credential forwarding."""

    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise GenerationResponseError(f"{service} returned an unsupported download URL")
    safe_headers: Mapping[str, str] | None = None
    if authenticated_origin is not None and _origin(url) == _origin(authenticated_origin):
        safe_headers = headers
    try:
        async with client.stream("GET", url, headers=safe_headers) as response:
            if response.is_error:
                raise GenerationResponseError(
                    f"{service} download returned HTTP {response.status_code}"
                )
            length = response.headers.get("content-length")
            if length and length.isdigit() and int(length) > max_bytes:
                raise GenerationTooLargeError(
                    f"{service} media exceeds the configured byte limit"
                )
            chunks: list[bytes] = []
            total = 0
            async for chunk in response.aiter_bytes():
                total += len(chunk)
                if total > max_bytes:
                    raise GenerationTooLargeError(
                        f"{service} media exceeds the configured byte limit"
                    )
                chunks.append(chunk)
    except (httpx.TimeoutException, httpx.TransportError) as exc:
        raise GenerationTransportError(
            f"{service} download failed: {type(exc).__name__}"
        ) from exc
    return b"".join(chunks)


async def bounded_download_to_path(
    client: httpx.AsyncClient,
    url: str,
    destination: str | Path,
    *,
    max_bytes: int,
    service: str,
    headers: Mapping[str, str] | None = None,
    authenticated_origin: str | None = None,
) -> Path:
    """Download bounded bytes and atomically replace the destination."""

    destination_path = Path(destination)
    temporary = destination_path.with_name(f".{destination_path.name}.part")
    try:
        content = await bounded_download(
            client,
            url,
            max_bytes=max_bytes,
            service=service,
            headers=headers,
            authenticated_origin=authenticated_origin,
        )
        temporary.write_bytes(content)
        os.replace(temporary, destination_path)
        return destination_path
    finally:
        if temporary.exists():
            temporary.unlink()


def _origin(url: str) -> tuple[str, str, int | None]:
    parsed = urlsplit(url)
    return parsed.scheme.lower(), (parsed.hostname or "").lower(), parsed.port


def _error_detail(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        text = response.text.strip()
        return text[:200] if text else "no response detail"
    if isinstance(data, Mapping):
        error = data.get("error")
        if isinstance(error, Mapping):
            detail = error.get("message") or error.get("detail")
            if detail:
                return str(detail)[:200]
        detail = data.get("message") or data.get("detail")
        if detail:
            return str(detail)[:200]
    return "no response detail"
