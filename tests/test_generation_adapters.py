from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from pydantic import ValidationError

from omni_rewriter.adapters import (
    GenerationConfigurationError,
    GenerationResponseError,
    GenerationTooLargeError,
    GenerationTransportError,
    HunyuanImageVLLMClient,
    HunyuanImageVLLMClientConfig,
    OmniVideosClient,
    OmniVideosClientConfig,
    OpenAIImagesClient,
    OpenAIImagesClientConfig,
    WanOmniAdapter,
)
from omni_rewriter.adapters.base import bounded_download
from omni_rewriter.config import Settings
from omni_rewriter.models import MediaReference, MediaRole, MediaType, RewriteRequest, TaskType


def image_request(**metadata: str) -> RewriteRequest:
    return RewriteRequest(prompt="raw", task=TaskType.T2I, metadata=metadata)


def video_request(
    *,
    duration: float = 5,
    media: list[MediaReference] | None = None,
    metadata: dict[str, str] | None = None,
) -> RewriteRequest:
    return RewriteRequest(
        prompt="raw",
        duration_seconds=duration,
        media=media or [],
        metadata=metadata or {},
    )


def frame(role: MediaRole, uri: str) -> MediaReference:
    return MediaReference(media_type=MediaType.IMAGE, role=role, uri=uri)


def openai_images(
    client: httpx.AsyncClient,
    *,
    max_download_bytes: int = 64,
) -> OpenAIImagesClient:
    return OpenAIImagesClient(
        OpenAIImagesClientConfig(
            base_url="https://images.test/v1",
            api_key="image-secret",
            model="qwen-image",
            max_download_bytes=max_download_bytes,
        ),
        client=client,
    )


def omni_videos(
    client: httpx.AsyncClient,
    *,
    transport: str = "json",
    max_download_bytes: int = 64,
    max_reference_bytes: int = 64,
) -> OmniVideosClient:
    return OmniVideosClient(
        OmniVideosClientConfig(
            base_url="https://video.test/v1",
            api_key="video-secret",
            transport=transport,
            poll_interval=0.001,
            max_download_bytes=max_download_bytes,
            max_reference_bytes=max_reference_bytes,
        ),
        mapper=WanOmniAdapter(model="wan-test"),
        client=client,
    )


def test_openai_images_payload_is_bounded_and_testable() -> None:
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(500)))
    adapter = openai_images(client)
    payload = adapter.build_payload(
        image_request(size="1024x1024"),
        "expanded prompt",
        extra={"seed": 7, "quality": "standard"},
    )
    assert payload == {
        "model": "qwen-image",
        "prompt": "expanded prompt",
        "n": 1,
        "response_format": "b64_json",
        "size": "1024x1024",
        "seed": 7,
        "quality": "standard",
    }
    with pytest.raises(GenerationConfigurationError, match="unsupported"):
        adapter.build_payload(image_request(), "p", extra={"model": "override"})


@pytest.mark.asyncio
async def test_openai_images_decodes_b64_and_data_uri() -> None:
    calls: list[dict[str, Any]] = []
    values = [
        base64.b64encode(b"first").decode(),
        "data:image/png;base64," + base64.b64encode(b"second").decode(),
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(json.loads(request.content))
        return httpx.Response(200, json={"data": [{"b64_json": value} for value in values]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = openai_images(client)
    assert await adapter.generate_many(image_request(), "expanded", n=2) == [b"first", b"second"]
    assert calls[0]["n"] == 2
    assert calls[0]["prompt"] == "expanded"
    await client.aclose()


@pytest.mark.asyncio
async def test_openai_images_downloads_url_without_leaking_cross_origin_key() -> None:
    seen_authorization: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "images.test":
            return httpx.Response(200, json={"data": [{"url": "https://cdn.test/image.png"}]})
        seen_authorization.append(request.headers.get("authorization"))
        return httpx.Response(200, content=b"image")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    assert await openai_images(client).generate(image_request(), "expanded") == b"image"
    assert seen_authorization == [None]
    await client.aclose()


@pytest.mark.asyncio
async def test_openai_images_enforces_b64_and_url_limits() -> None:
    responses = iter(
        [
            httpx.Response(
                200,
                json={"data": [{"b64_json": base64.b64encode(b"large").decode()}]},
            ),
            httpx.Response(200, json={"data": [{"url": "https://cdn.test/image.png"}]}),
            httpx.Response(200, content=b"large"),
        ]
    )
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda _: next(responses)))
    adapter = openai_images(client, max_download_bytes=2)
    with pytest.raises(GenerationTooLargeError, match="limit"):
        await adapter.generate(image_request(), "p")
    with pytest.raises(GenerationTooLargeError, match="limit"):
        await adapter.generate(image_request(), "p")
    await client.aclose()


@pytest.mark.asyncio
async def test_openai_images_rejects_malformed_responses() -> None:
    responses = iter(
        [
            httpx.Response(200, json={"data": []}),
            httpx.Response(200, json={"data": [{}]}),
            httpx.Response(200, json={"data": [{"b64_json": "!!!"}]}),
        ]
    )
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda _: next(responses)))
    adapter = openai_images(client)
    for expected in ("omitted", "omitted", "invalid base64"):
        with pytest.raises(GenerationResponseError, match=expected):
            await adapter.generate(image_request(), "p")
    await client.aclose()


def test_hunyuan_payload_matches_local_vllm_evidence() -> None:
    adapter = HunyuanImageVLLMClient(
        HunyuanImageVLLMClientConfig(model="hunyuan", width=1024, height=1024)
    )
    payload = adapter.build_payload(
        image_request(width="768", height="1280", seed="42"),
        "expanded",
    )
    assert payload["task_type"] == "hunyuan_image3"
    assert payload["model"] == "hunyuan"
    assert payload["max_completion_tokens"] == 1
    assert payload["seed"] == 42
    assert payload["messages"][-1] == {"role": "user", "content": "expanded"}
    assert payload["task_extra_kwargs"] == {
        "diff_infer_steps": 50,
        "use_system_prompt": "None",
        "bot_task": "image",
        "image_size": "1280x768",
    }
    with pytest.raises(GenerationConfigurationError, match="cannot override"):
        adapter.build_payload(image_request(), "p", task_extra={"bot_task": "auto"})


@pytest.mark.asyncio
async def test_hunyuan_decodes_top_level_image_and_bounds_it() -> None:
    payloads: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payloads.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={"image": "data:image/png;base64," + base64.b64encode(b"png").decode()},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = HunyuanImageVLLMClient(
        HunyuanImageVLLMClientConfig(
            base_url="https://hunyuan.test",
            api_key="secret",
            max_image_bytes=3,
        ),
        client=client,
    )
    assert await adapter.generate(image_request(), "expanded") == b"png"
    assert payloads[0]["task_type"] == "hunyuan_image3"
    adapter.config.max_image_bytes = 2
    with pytest.raises(GenerationTooLargeError):
        await adapter.generate(image_request(), "expanded")
    await client.aclose()


@pytest.mark.asyncio
async def test_hunyuan_requires_top_level_image() -> None:
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json={"choices": [{"message": {"content": "x"}}]})
        )
    )
    adapter = HunyuanImageVLLMClient(HunyuanImageVLLMClientConfig(), client=client)
    with pytest.raises(GenerationResponseError, match="top-level image"):
        await adapter.generate(image_request(), "p")
    await client.aclose()


def test_wan_payload_maps_duration_size_seed_and_frames() -> None:
    request = video_request(
        duration=6,
        media=[
            frame(MediaRole.FIRST_FRAME, "https://assets.test/first.png"),
            frame(MediaRole.LAST_FRAME, "https://assets.test/last.png"),
        ],
        metadata={"width": "1280", "height": "720", "seed": "9"},
    )
    payload = WanOmniAdapter(model="wan").build_payload(
        request,
        "expanded",
        extra={"num_inference_steps": 30, "guidance_scale": 5.0},
    )
    assert payload == {
        "model": "wan",
        "prompt": "expanded",
        "size": "1280x720",
        "seconds": 6,
        "seed": 9,
        "input_reference": "https://assets.test/first.png",
        "last_frame": "https://assets.test/last.png",
        "num_inference_steps": 30,
        "guidance_scale": 5.0,
    }


@pytest.mark.parametrize(
    ("rewrite_request", "match"),
    [
        (video_request(duration=1.5), "integer"),
        (video_request(duration=21), "integer"),
        (video_request(metadata={"size": "bad"}), "WIDTHxHEIGHT"),
    ],
)
def test_wan_payload_rejects_invalid_generation_values(
    rewrite_request: RewriteRequest, match: str
) -> None:
    with pytest.raises(GenerationConfigurationError, match=match):
        WanOmniAdapter().build_payload(rewrite_request, "p")


@pytest.mark.asyncio
async def test_omni_videos_json_submit_poll_and_content_download(tmp_path: Path) -> None:
    queries = 0
    posts: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal queries
        if request.method == "POST":
            posts.append(json.loads(request.content))
            return httpx.Response(200, json={"id": "video-1"})
        if request.url.path.endswith("/content"):
            return httpx.Response(200, content=b"video")
        queries += 1
        status = "queued" if queries == 1 else "completed"
        return httpx.Response(200, json={"status": status})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = omni_videos(client)
    task_id = await adapter.submit(video_request(), "expanded")
    result = await adapter.wait(task_id)
    target = tmp_path / "result.mp4"
    assert await adapter.download(task_id, target, result=result) == target
    assert target.read_bytes() == b"video"
    assert posts == [
        {
            "model": "wan-test",
            "prompt": "expanded",
            "size": "832x480",
            "seconds": 5,
        }
    ]
    await client.aclose()


@pytest.mark.asyncio
async def test_omni_videos_multipart_uploads_bounded_data_reference() -> None:
    image = base64.b64encode(b"png").decode()
    bodies: list[bytes] = []
    content_types: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(request.content)
        content_types.append(request.headers["content-type"])
        return httpx.Response(200, json={"id": "video-1"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = omni_videos(client, transport="multipart")
    request = video_request(media=[frame(MediaRole.FIRST_FRAME, f"data:image/png;base64,{image}")])
    assert await adapter.submit(request, "expanded") == "video-1"
    assert content_types[0].startswith("multipart/form-data; boundary=")
    assert b'name="input_reference"; filename="input_reference.png"' in bodies[0]
    assert b"expanded" in bodies[0]
    adapter.config.max_reference_bytes = 2
    with pytest.raises(GenerationTooLargeError):
        await adapter.submit(request, "expanded")
    await client.aclose()


@pytest.mark.asyncio
async def test_omni_videos_fails_closed_and_bounds_download() -> None:
    responses = iter(
        [
            httpx.Response(200, json={"status": "mystery"}),
            httpx.Response(200, content=b"large"),
        ]
    )
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda _: next(responses)))
    adapter = omni_videos(client, max_download_bytes=2)
    with pytest.raises(GenerationResponseError, match="unknown status"):
        await adapter.wait("job")
    with pytest.raises(GenerationTooLargeError):
        await adapter.download_bytes("job", result={"status": "completed"})
    await client.aclose()


@pytest.mark.asyncio
async def test_omni_submit_transport_failure_is_not_retried() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ConnectError("offline")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    with pytest.raises(GenerationTransportError, match="ConnectError"):
        await omni_videos(client).submit(video_request(), "expanded")
    assert calls == 1
    await client.aclose()


def test_generation_configs_are_strict_and_settings_build_clients(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValidationError):
        OmniVideosClientConfig(unknown=True)  # type: ignore[call-arg]
    monkeypatch.setenv("OMNI_WRITER_VIDEO_TRANSPORT", "json")
    monkeypatch.setenv("OMNI_WRITER_IMAGE_RESPONSE_FORMAT", "url")
    monkeypatch.setenv("OMNI_WRITER_WAN_DEFAULT_SIZE", "640x480")
    settings = Settings.from_env()
    assert settings.omni_videos_client_config().transport == "json"
    assert settings.openai_images_client_config().response_format == "url"
    assert settings.wan_omni_adapter().default_size == "640x480"


@pytest.mark.asyncio
async def test_bounded_download_rejects_private_hosts() -> None:
    client = httpx.AsyncClient()
    with pytest.raises(GenerationResponseError, match="non-public"):
        await bounded_download(
            client,
            "http://127.0.0.1/secret.bin",
            max_bytes=16,
            service="test",
        )
    await client.aclose()
