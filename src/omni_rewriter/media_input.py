"""Bounded media loading and Qwen-compatible multimodal message construction."""

from __future__ import annotations

import asyncio
import base64
import binascii
import ipaddress
import mimetypes
import socket
from pathlib import Path
from urllib.parse import unquote_to_bytes, urlsplit

import httpx
from pydantic import Field

from .errors import MediaMIMEError, MediaTooLargeError, MediaURIError
from .models import MediaReference, MediaType
from .models.common import StrictModel

_MIME_PREFIX = {
    MediaType.IMAGE: "image/",
    MediaType.VIDEO: "video/",
    MediaType.AUDIO: "audio/",
}
_ALLOWED_MIMES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "video/mp4",
        "video/webm",
        "video/quicktime",
        "audio/mpeg",
        "audio/mp4",
        "audio/wav",
        "audio/x-wav",
        "audio/webm",
        "audio/ogg",
        "audio/flac",
    }
)


class MediaInputConfig(StrictModel):
    """Security and resource limits for caller-owned media."""

    max_bytes: int = Field(default=20 * 1024 * 1024, gt=0)
    timeout: float = Field(default=30.0, gt=0)
    allowed_mime_types: frozenset[str] = _ALLOWED_MIMES
    allow_private_hosts: bool = False
    allow_local_files: bool = True
    max_redirects: int = Field(default=3, ge=0, le=10)


class PreparedMedia(StrictModel):
    """Validated media represented as an inline data URI."""

    media_type: MediaType
    mime_type: str
    data_uri: str
    byte_length: int = Field(ge=0)
    name: str | None = None

    def qwen_content_part(self) -> dict[str, object]:
        """Return an OpenAI-compatible Qwen multimodal content part."""

        key = f"{self.media_type.value}_url"
        return {"type": key, key: {"url": self.data_uri}}


class MediaPreparer:
    """Load local, HTTP(S), or data-URI media with strict bounds."""

    def __init__(
        self,
        config: MediaInputConfig | None = None,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config or MediaInputConfig()
        self._client = client
        self._owns_client = client is None

    async def __aenter__(self) -> "MediaPreparer":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    async def prepare(self, reference: MediaReference) -> PreparedMedia:
        """Validate and inline one media reference."""

        uri = reference.uri
        source_mime: str | None
        if uri.startswith("data:"):
            data, declared = self._decode_data_uri(uri)
            source_mime = declared
        else:
            parsed = urlsplit(uri)
            if parsed.scheme in {"http", "https"}:
                data, source_mime = await self._download(uri)
            elif parsed.scheme:
                raise MediaURIError(f"unsupported media URI scheme: {parsed.scheme!r}")
            else:
                if not self.config.allow_local_files:
                    raise MediaURIError("local media paths are disabled for this MediaPreparer")
                data, source_mime = await self._read_local(Path(uri))

        mime = self._validate_mime(
            reference.media_type,
            data,
            reference.mime_type or source_mime,
        )
        encoded = base64.b64encode(data).decode("ascii")
        return PreparedMedia(
            media_type=reference.media_type,
            mime_type=mime,
            data_uri=f"data:{mime};base64,{encoded}",
            byte_length=len(data),
            name=reference.name,
        )

    async def prepare_message(
        self,
        text: str,
        media: list[MediaReference],
    ) -> dict[str, object]:
        """Build one Qwen user message while preserving input order."""

        prepared = await asyncio.gather(*(self.prepare(item) for item in media))
        content: list[dict[str, object]] = [{"type": "text", "text": text}]
        content.extend(item.qwen_content_part() for item in prepared)
        return {"role": "user", "content": content}

    async def _read_local(self, path: Path) -> tuple[bytes, str | None]:
        try:
            size = await asyncio.to_thread(path.stat)
        except OSError as exc:
            raise MediaURIError(f"cannot access local media: {path.name!r}") from exc
        if not path.is_file():
            raise MediaURIError(f"local media is not a regular file: {path.name!r}")
        self._check_size(size.st_size)

        def read_bounded() -> bytes:
            with path.open("rb") as stream:
                return stream.read(self.config.max_bytes + 1)

        try:
            data = await asyncio.to_thread(read_bounded)
        except OSError as exc:
            raise MediaURIError(f"cannot read local media: {path.name!r}") from exc
        self._check_size(len(data))
        guessed, _ = mimetypes.guess_type(path.name)
        return data, guessed

    async def _download(self, uri: str) -> tuple[bytes, str | None]:
        current = uri
        for redirect in range(self.config.max_redirects + 1):
            await self._check_remote_host(current)
            client = self._get_client()
            try:
                async with client.stream("GET", current) as response:
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            raise MediaURIError("media redirect omitted a location")
                        if redirect >= self.config.max_redirects:
                            raise MediaURIError("media redirect limit exceeded")
                        current = str(response.url.join(location))
                        continue
                    if response.is_error:
                        raise MediaURIError(f"media server returned HTTP {response.status_code}")
                    length = response.headers.get("content-length")
                    if length and length.isdigit():
                        self._check_size(int(length))
                    chunks: list[bytes] = []
                    total = 0
                    async for chunk in response.aiter_bytes():
                        total += len(chunk)
                        self._check_size(total)
                        chunks.append(chunk)
                    content_type = response.headers.get("content-type", "").split(";", 1)[0]
                    return b"".join(chunks), content_type or None
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                raise MediaURIError(f"failed to download media: {type(exc).__name__}") from exc
        raise MediaURIError("media redirect loop terminated unexpectedly")

    async def _check_remote_host(self, uri: str) -> None:
        parsed = urlsplit(uri)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise MediaURIError("remote media requires an HTTP(S) URL with a hostname")
        if self.config.allow_private_hosts:
            return
        try:
            records = await asyncio.get_running_loop().getaddrinfo(
                parsed.hostname,
                parsed.port or (443 if parsed.scheme == "https" else 80),
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror as exc:
            raise MediaURIError("remote media hostname could not be resolved") from exc
        for record in records:
            address = ipaddress.ip_address(record[4][0])
            if not address.is_global:
                raise MediaURIError("remote media hostname resolves to a non-public address")

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout,
                follow_redirects=False,
            )
        return self._client

    def _decode_data_uri(self, uri: str) -> tuple[bytes, str]:
        try:
            header, payload = uri.split(",", 1)
        except ValueError as exc:
            raise MediaURIError("malformed data URI") from exc
        metadata = header[5:].split(";")
        mime = metadata[0].lower()
        if not mime:
            raise MediaMIMEError("data URI must declare a MIME type")
        try:
            if metadata[-1].lower() == "base64":
                estimated = (len(payload) * 3) // 4
                self._check_size(estimated)
                data = base64.b64decode(payload, validate=True)
            else:
                data = unquote_to_bytes(payload)
        except (binascii.Error, ValueError) as exc:
            raise MediaURIError("data URI payload is invalid") from exc
        self._check_size(len(data))
        return data, mime

    def _check_size(self, size: int) -> None:
        if size > self.config.max_bytes:
            raise MediaTooLargeError(
                f"media is {size} bytes; limit is {self.config.max_bytes} bytes"
            )

    def _validate_mime(
        self,
        media_type: MediaType,
        data: bytes,
        declared: str | None,
    ) -> str:
        mime = (declared or "").lower().split(";", 1)[0].strip()
        sniffed = _sniff_mime(data)
        if not mime:
            mime = sniffed or ""
        if not mime:
            raise MediaMIMEError("media MIME type could not be determined")
        if mime not in self.config.allowed_mime_types:
            raise MediaMIMEError(f"media MIME type is not allowed: {mime!r}")
        if not mime.startswith(_MIME_PREFIX[media_type]):
            raise MediaMIMEError(f"MIME type {mime!r} does not match {media_type.value!r} media")
        if sniffed and sniffed != mime and not {sniffed, mime} <= {"audio/wav", "audio/x-wav"}:
            raise MediaMIMEError(f"declared MIME type {mime!r} conflicts with detected {sniffed!r}")
        return mime


def _sniff_mime(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    if data.startswith(b"RIFF") and data[8:12] == b"WAVE":
        return "audio/wav"
    if data.startswith(b"fLaC"):
        return "audio/flac"
    if data.startswith(b"OggS"):
        return "audio/ogg"
    if data.startswith(b"\x1aE\xdf\xa3"):
        return "video/webm"
    if len(data) >= 12 and data[4:8] == b"ftyp":
        brand = data[8:12]
        if brand in {b"M4A ", b"M4B ", b"mp4a"}:
            return "audio/mp4"
        if brand == b"qt  ":
            return "video/quicktime"
        return "video/mp4"
    if data.startswith(b"ID3") or data[:2] in {
        b"\xff\xfb",
        b"\xff\xf3",
        b"\xff\xf2",
    }:
        return "audio/mpeg"
    return None
