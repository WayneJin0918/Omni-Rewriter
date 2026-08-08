from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from omni_rewriter.api import create_app
from omni_rewriter.backends import ScriptedBackend
from omni_rewriter.config import Settings
from omni_rewriter.models import MediaReference, MediaRole, MediaType, RewriteRequest, TaskType
from omni_rewriter.service import expand as expand_service

TINY_PNG = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def _patch_scripted(monkeypatch: pytest.MonkeyPatch, responses: list[str]) -> ScriptedBackend:
    backend = ScriptedBackend(responses)
    monkeypatch.setattr(
        "omni_rewriter.service.OpenAICompatibleBackend",
        lambda _config: backend,
    )
    return backend


@pytest.mark.asyncio
async def test_service_expand_seedream(
    monkeypatch: pytest.MonkeyPatch,
    analysis_output: dict[str, Any],
    seedream_output: dict[str, Any],
) -> None:
    _patch_scripted(
        monkeypatch,
        [json.dumps(analysis_output), json.dumps(seedream_output)],
    )
    result = await expand_service(
        RewriteRequest(
            prompt="Neon storefront poster",
            task=TaskType.T2I,
            metadata={"image_pe_profile": "seedream"},
        ),
        Settings(),
    )
    assert result.output.task.value == "t2i"
    assert result.repairs == 0


@pytest.mark.asyncio
async def test_service_expand_respects_allow_local_media(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    png_bytes: bytes,
) -> None:
    path = tmp_path / "disk.png"
    path.write_bytes(png_bytes)
    _patch_scripted(monkeypatch, ["{}"])
    with pytest.raises(Exception, match="local media paths are disabled"):
        await expand_service(
            RewriteRequest(
                prompt="edit",
                task=TaskType.IMAGE_EDIT,
                media=[
                    MediaReference(
                        media_type=MediaType.IMAGE,
                        role=MediaRole.REFERENCE,
                        uri=str(path),
                    )
                ],
            ),
            Settings(allow_local_media=False),
        )


def test_api_expand_rejects_local_media_by_default(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    png_bytes: bytes,
) -> None:
    path = tmp_path / "secret.png"
    path.write_bytes(png_bytes)
    monkeypatch.delenv("OMNI_WRITER_ALLOW_LOCAL_MEDIA", raising=False)
    _patch_scripted(monkeypatch, ["{}"])
    client = TestClient(create_app(Settings(allow_local_media=True)))
    response = client.post(
        "/v1/expand",
        json={
            "prompt": "edit from disk",
            "task": "image_edit",
            "media": [
                {
                    "media_type": "image",
                    "role": "reference",
                    "uri": str(path),
                }
            ],
        },
    )
    assert response.status_code == 502
    assert "local media" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_service_expand_qwen_edit_data_uri(
    monkeypatch: pytest.MonkeyPatch,
    analysis_output: dict[str, Any],
    qwen_edit_output: dict[str, Any],
) -> None:
    _patch_scripted(
        monkeypatch,
        [json.dumps(analysis_output), json.dumps(qwen_edit_output)],
    )
    result = await expand_service(
        RewriteRequest(
            prompt="Change dress color",
            task=TaskType.IMAGE_EDIT,
            media=[
                MediaReference(
                    media_type=MediaType.IMAGE,
                    role=MediaRole.REFERENCE,
                    uri=TINY_PNG,
                )
            ],
        ),
        Settings(),
    )
    assert result.output.task.value == "image_edit"
