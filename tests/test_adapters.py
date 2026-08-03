from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
import pytest

from omni_writer.adapters.h3 import H3Client, H3ClientConfig
from omni_writer.adapters.minimax import MiniMaxClient, MiniMaxClientConfig
from omni_writer.errors import (
    BackendConfigurationError,
    BackendResponseError,
    BackendTransportError,
)
from omni_writer.models import MediaReference, MediaRole, MediaType, RewriteRequest


def request(
    *,
    duration: float = 6,
    media: list[MediaReference] | None = None,
    metadata: dict[str, str] | None = None,
) -> RewriteRequest:
    return RewriteRequest(
        prompt="A kite turns in the wind.",
        duration_seconds=duration,
        media=media or [],
        metadata=metadata or {},
    )


def frame(role: MediaRole, uri: str = "data:image/png;base64,AA==") -> MediaReference:
    return MediaReference(media_type=MediaType.IMAGE, role=role, uri=uri)


def source_video() -> MediaReference:
    return MediaReference(
        media_type=MediaType.VIDEO,
        role=MediaRole.SOURCE,
        uri="data:video/mp4;base64,AA==",
    )


def h3_client(client: httpx.AsyncClient | None = None, **kwargs: Any) -> H3Client:
    return H3Client(H3ClientConfig(base_url="http://h3.test", **kwargs), client=client)


def minimax_client(client: httpx.AsyncClient | None = None, **kwargs: Any) -> MiniMaxClient:
    return MiniMaxClient(
        MiniMaxClientConfig(api_key="secret", base_url="http://minimax.test", **kwargs),
        client=client,
    )


def test_h3_payload_exact_official_fields() -> None:
    payload = h3_client().build_payload(
        request(metadata={"seed": "7", "short_edge": "1080"}),
        "expanded",
    )
    assert set(payload) == {"task", "prompt", "conditions", "target", "seed"}
    assert payload == {
        "task": "t2va",
        "prompt": "expanded",
        "conditions": [],
        "target": {
            "short_edge": 1080,
            "aspect_ratio": "16:9",
            "duration_seconds": 6,
        },
        "seed": 7,
    }


@pytest.mark.parametrize("duration", [4, 15])
def test_h3_duration_bounds(duration: int) -> None:
    assert (
        h3_client().build_payload(request(duration=duration), "p")["target"]["duration_seconds"]
        == duration
    )


@pytest.mark.parametrize("duration", [3, 16, 4.5])
def test_h3_rejects_invalid_duration(duration: float) -> None:
    with pytest.raises(BackendConfigurationError, match="integer from 4 through 15"):
        h3_client().build_payload(request(duration=duration), "p")


def test_h3_conditions_and_task_mapping() -> None:
    payload = h3_client().build_payload(
        request(
            media=[
                frame(MediaRole.FIRST_FRAME, "first.png"),
                frame(MediaRole.LAST_FRAME, "last.png"),
            ]
        ),
        "p",
    )
    assert payload["task"] == "fl2va"
    assert payload["conditions"][0]["frame_index"] == 0
    assert payload["conditions"][1]["frame_index"] == -1


def test_h3_rejects_undocumented_extra() -> None:
    with pytest.raises(BackendConfigurationError, match="unsupported"):
        h3_client().build_payload(request(), "p", extra={"seconds": 6})


@pytest.mark.asyncio
async def test_h3_submit_query_and_http_errors() -> None:
    def handler(req: httpx.Request) -> httpx.Response:
        if req.method == "POST":
            return httpx.Response(200, json={"id": "job-1"})
        return httpx.Response(500)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = h3_client(client)
    assert await adapter.submit(request(), "expanded") == "job-1"
    with pytest.raises(BackendResponseError, match="HTTP 500"):
        await adapter.query("job-1")
    await client.aclose()


@pytest.mark.asyncio
async def test_h3_wait_statuses(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = h3_client(poll_interval=0.001)
    results = iter([{"status": "processing"}, {"status": "completed", "url": "x"}])

    async def query(_: str) -> dict[str, Any]:
        return next(results)

    async def no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(adapter, "query", query)
    monkeypatch.setattr("omni_writer.adapters.h3.asyncio.sleep", no_sleep)
    assert (await adapter.wait("job"))["status"] == "completed"

    async def failed(_: str) -> dict[str, Any]:
        return {"status": "failed", "message": "bad input"}

    monkeypatch.setattr(adapter, "query", failed)
    with pytest.raises(BackendResponseError, match="bad input"):
        await adapter.wait("job")


@pytest.mark.asyncio
async def test_h3_wait_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = h3_client(poll_timeout=0.001, poll_interval=0.001)

    async def pending(_: str) -> dict[str, Any]:
        return {"status": "queued"}

    monkeypatch.setattr(adapter, "query", pending)
    with pytest.raises(BackendTransportError, match="timed out"):
        await adapter.wait("job")


@pytest.mark.asyncio
async def test_h3_download_and_bound(tmp_path: Path) -> None:
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=b"video"))
    )
    adapter = h3_client(client, max_download_bytes=8)
    target = tmp_path / "out.mp4"
    assert await adapter.download("job", target, result={"url": "http://cdn.test/v"}) == target
    assert target.read_bytes() == b"video"
    adapter.config.max_download_bytes = 2
    with pytest.raises(BackendResponseError, match="limit"):
        await adapter.download("job", target, result={"url": "http://cdn.test/v"})
    assert not (tmp_path / ".out.mp4.part").exists()
    await client.aclose()


def test_minimax_context_payload() -> None:
    payload = MiniMaxClient.build_context_payload(request(media=[frame(MediaRole.FIRST_FRAME)]))
    assert payload["duration"] == 6
    assert payload["ratio"] == "adaptive"
    assert payload["content"][1]["role"] == "first_frame"


def test_minimax_regeneration_payload_resolution() -> None:
    payload = MiniMaxClient.build_regeneration_payload(
        request(
            media=[frame(MediaRole.FIRST_FRAME), source_video()],
            metadata={"resolution": "1080P"},
        )
    )
    assert set(payload) == {"model", "content", "resolution"}
    assert payload["resolution"] == "1080P"
    assert payload["content"][2]["role"] == "base_video"


def test_minimax_regeneration_validation() -> None:
    with pytest.raises(BackendConfigurationError, match="source video"):
        MiniMaxClient.build_regeneration_payload(request())
    with pytest.raises(BackendConfigurationError, match="resolution"):
        MiniMaxClient.build_regeneration_payload(
            request(media=[source_video()], metadata={"resolution": "4K"})
        )


@pytest.mark.asyncio
async def test_minimax_submit_and_api_error() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(200, json={"task_id": "mm-1", "base_resp": {"status_code": 0}})
        return httpx.Response(
            200,
            json={"base_resp": {"status_code": 1001, "status_msg": "denied"}},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = minimax_client(client)
    assert await adapter.submit_h3_context_ir(request()) == "mm-1"
    with pytest.raises(BackendResponseError, match="1001"):
        await adapter.query("mm-1")
    await client.aclose()


@pytest.mark.asyncio
async def test_minimax_status_and_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = minimax_client(poll_timeout=0.001, poll_interval=0.001)

    async def failed(_: str) -> dict[str, Any]:
        return {"task": {"status": "failed", "message": "generation failed"}}

    monkeypatch.setattr(adapter, "query", failed)
    with pytest.raises(BackendResponseError, match="generation failed"):
        await adapter.wait("job")

    async def pending(_: str) -> dict[str, Any]:
        return {"task": {"status": "processing"}}

    monkeypatch.setattr(adapter, "query", pending)
    with pytest.raises(BackendTransportError, match="timed out"):
        await adapter.wait("job")
