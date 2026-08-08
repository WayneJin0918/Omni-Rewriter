from __future__ import annotations

import json
from pathlib import Path

import pytest

from omni_rewriter.agent import RewriteAgent, RewriteAgentConfig
from omni_rewriter.backends import ScriptedBackend
from omni_rewriter.errors import MediaURIError, RepairExhaustedError, StructuredOutputError
from omni_rewriter.media_input import MediaInputConfig, MediaPreparer
from omni_rewriter.models import MediaReference, MediaRole, MediaType, RewriteRequest, TaskType


def request() -> RewriteRequest:
    return RewriteRequest(prompt="A paper kite climbs.", duration_seconds=6)


TINY_PNG = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


@pytest.mark.asyncio
async def test_agent_happy_path(
    analysis_output: dict[str, object],
    base_output: dict[str, object],
) -> None:
    backend = ScriptedBackend([json.dumps(analysis_output), json.dumps(base_output)])
    result = await RewriteAgent(backend).run(request())
    assert result.repairs == 0
    assert result.output.task.value == "t2va"
    assert len(backend.calls) == 2


@pytest.mark.asyncio
async def test_agent_repairs_invalid_draft(
    analysis_output: dict[str, object],
    base_output: dict[str, object],
) -> None:
    backend = ScriptedBackend(
        [json.dumps(analysis_output), '{"task": "t2va"}', json.dumps(base_output)]
    )
    result = await RewriteAgent(
        backend,
        config=RewriteAgentConfig(max_repairs=1),
    ).run(request())
    assert result.repairs == 1
    assert "validation_errors" in str(backend.calls[2][1]["content"])


@pytest.mark.asyncio
async def test_agent_exhaustion(analysis_output: dict[str, object]) -> None:
    backend = ScriptedBackend([json.dumps(analysis_output), "{}", "{}"])
    with pytest.raises(RepairExhaustedError, match="after 1 repairs"):
        await RewriteAgent(
            backend,
            config=RewriteAgentConfig(max_repairs=1),
        ).run(request())
    assert len(backend.calls) == 3


@pytest.mark.asyncio
async def test_agent_rejects_invalid_analysis() -> None:
    backend = ScriptedBackend(["not-json"])
    with pytest.raises(StructuredOutputError, match="AnalysisPlan"):
        await RewriteAgent(backend).run(request())


@pytest.mark.asyncio
async def test_agent_accepts_fenced_json(
    analysis_output: dict[str, object],
    base_output: dict[str, object],
) -> None:
    backend = ScriptedBackend(
        [
            f"```json\n{json.dumps(analysis_output)}\n```",
            f"```\n{json.dumps(base_output)}\n```",
        ]
    )
    result = await RewriteAgent(backend).run(request())
    assert result.output.duration_seconds == 6


@pytest.mark.asyncio
async def test_agent_repairs_duration_mismatch(
    analysis_output: dict[str, object],
    base_output: dict[str, object],
) -> None:
    wrong = {**base_output, "duration_seconds": "5"}
    backend = ScriptedBackend(
        [json.dumps(analysis_output), json.dumps(wrong), json.dumps(base_output)]
    )
    result = await RewriteAgent(
        backend,
        config=RewriteAgentConfig(max_repairs=1),
    ).run(request())
    assert result.repairs == 1


@pytest.mark.asyncio
async def test_agent_seedream_t2i(
    analysis_output: dict[str, object],
    seedream_output: dict[str, object],
) -> None:
    backend = ScriptedBackend([json.dumps(analysis_output), json.dumps(seedream_output)])
    result = await RewriteAgent(backend).run(
        RewriteRequest(
            prompt="Create a rain-soaked neon storefront poster.",
            task=TaskType.T2I,
            metadata={"image_pe_profile": "seedream"},
        )
    )
    assert result.output.task.value == "t2i"
    assert "Summer Special" in result.output.render()


@pytest.mark.asyncio
async def test_agent_qwen_image_edit(
    analysis_output: dict[str, object],
    qwen_edit_output: dict[str, object],
) -> None:
    backend = ScriptedBackend([json.dumps(analysis_output), json.dumps(qwen_edit_output)])
    result = await RewriteAgent(backend).run(
        RewriteRequest(
            prompt="Change the dress to deep emerald silk.",
            task=TaskType.IMAGE_EDIT,
            media=[
                MediaReference(
                    media_type=MediaType.IMAGE,
                    role=MediaRole.REFERENCE,
                    uri=TINY_PNG,
                    name="ref.png",
                )
            ],
        )
    )
    assert result.output.task.value == "image_edit"
    assert result.output.render() == qwen_edit_output["prompt"]


@pytest.mark.asyncio
async def test_agent_ref2va(
    analysis_output: dict[str, object],
    ref_output: dict[str, object],
) -> None:
    backend = ScriptedBackend([json.dumps(analysis_output), json.dumps(ref_output)])
    result = await RewriteAgent(backend).run(
        RewriteRequest(
            prompt="Use the illustrated kite shape.",
            duration_seconds=6,
            media=[
                MediaReference(
                    media_type=MediaType.IMAGE,
                    role=MediaRole.REFERENCE,
                    uri=TINY_PNG,
                    name="kite.png",
                )
            ],
        )
    )
    assert "subject_definitions" in result.output.model_dump()
    assert result.output.duration_seconds == 6


@pytest.mark.asyncio
async def test_agent_denies_local_media_when_configured(
    tmp_path: Path,
    png_bytes: bytes,
) -> None:
    path = tmp_path / "local.png"
    path.write_bytes(png_bytes)
    backend = ScriptedBackend(["{}"])
    agent = RewriteAgent(
        backend,
        media_preparer=MediaPreparer(MediaInputConfig(allow_local_files=False)),
    )
    with pytest.raises(MediaURIError, match="local media paths are disabled"):
        await agent.run(
            RewriteRequest(
                prompt="edit from disk",
                task=TaskType.IMAGE_EDIT,
                media=[
                    MediaReference(
                        media_type=MediaType.IMAGE,
                        role=MediaRole.REFERENCE,
                        uri=str(path),
                    )
                ],
            )
        )
