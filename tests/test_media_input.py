from __future__ import annotations

import base64
from pathlib import Path

import httpx
import pytest

from omni_writer.errors import MediaMIMEError, MediaTooLargeError, MediaURIError
from omni_writer.media_input import MediaInputConfig, MediaPreparer
from omni_writer.models import MediaReference, MediaType


def image(uri: str, mime_type: str | None = None) -> MediaReference:
    return MediaReference(
        media_type=MediaType.IMAGE,
        uri=uri,
        mime_type=mime_type,
    )


@pytest.mark.asyncio
async def test_prepare_local_png(tmp_path: Path, png_bytes: bytes) -> None:
    path = tmp_path / "tiny.png"
    path.write_bytes(png_bytes)
    prepared = await MediaPreparer().prepare(image(str(path)))
    assert prepared.mime_type == "image/png"
    assert prepared.byte_length == len(png_bytes)
    assert prepared.data_uri.startswith("data:image/png;base64,")


@pytest.mark.asyncio
async def test_prepare_data_uri_and_message(png_bytes: bytes) -> None:
    uri = "data:image/png;base64," + base64.b64encode(png_bytes).decode()
    preparer = MediaPreparer()
    message = await preparer.prepare_message("inspect", [image(uri)])
    assert message["role"] == "user"
    assert len(message["content"]) == 2  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_data_uri_rejects_invalid_and_oversize(png_bytes: bytes) -> None:
    with pytest.raises(MediaURIError, match="invalid"):
        await MediaPreparer().prepare(image("data:image/png;base64,%%%"))
    uri = "data:image/png;base64," + base64.b64encode(png_bytes).decode()
    with pytest.raises(MediaTooLargeError):
        await MediaPreparer(MediaInputConfig(max_bytes=4)).prepare(image(uri))


@pytest.mark.asyncio
async def test_local_missing_and_mime_mismatch(tmp_path: Path, png_bytes: bytes) -> None:
    with pytest.raises(MediaURIError, match="cannot access"):
        await MediaPreparer().prepare(image(str(tmp_path / "missing.png")))
    path = tmp_path / "wrong.jpg"
    path.write_bytes(png_bytes)
    with pytest.raises(MediaMIMEError, match="conflicts"):
        await MediaPreparer().prepare(image(str(path), "image/jpeg"))


@pytest.mark.asyncio
async def test_http_download_is_bounded(
    monkeypatch: pytest.MonkeyPatch,
    png_bytes: bytes,
) -> None:
    async def permit(_: MediaPreparer, __: str) -> None:
        return None

    monkeypatch.setattr(MediaPreparer, "_check_remote_host", permit)
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                headers={"content-type": "image/png"},
                content=png_bytes,
            )
        )
    )
    prepared = await MediaPreparer(client=client).prepare(image("https://media.test/a.png"))
    assert prepared.byte_length == len(png_bytes)
    with pytest.raises(MediaTooLargeError):
        await MediaPreparer(MediaInputConfig(max_bytes=4), client=client).prepare(
            image("https://media.test/a.png")
        )
    await client.aclose()


@pytest.mark.asyncio
async def test_http_status_and_redirect_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    async def permit(_: MediaPreparer, __: str) -> None:
        return None

    monkeypatch.setattr(MediaPreparer, "_check_remote_host", permit)
    error_client = httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(404)))
    with pytest.raises(MediaURIError, match="HTTP 404"):
        await MediaPreparer(client=error_client).prepare(image("https://media.test/a.png"))
    await error_client.aclose()

    redirect_client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                302,
                headers={"location": "/again"},
                request=request,
            )
        )
    )
    with pytest.raises(MediaURIError, match="redirect limit"):
        await MediaPreparer(
            MediaInputConfig(max_redirects=0),
            client=redirect_client,
        ).prepare(image("https://media.test/a.png"))
    await redirect_client.aclose()


@pytest.mark.asyncio
async def test_ssrf_blocks_loopback() -> None:
    with pytest.raises(MediaURIError, match="non-public"):
        await MediaPreparer().prepare(image("http://127.0.0.1/private.png"))


@pytest.mark.asyncio
async def test_unsupported_uri_scheme() -> None:
    with pytest.raises(MediaURIError, match="unsupported"):
        await MediaPreparer().prepare(image("ftp://example.test/a.png"))
