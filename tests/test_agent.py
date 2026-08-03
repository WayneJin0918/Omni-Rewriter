from __future__ import annotations

import json

import pytest

from omni_writer.agent import RewriteAgent, RewriteAgentConfig
from omni_writer.backends import ScriptedBackend
from omni_writer.errors import RepairExhaustedError, StructuredOutputError
from omni_writer.models import RewriteRequest


def request() -> RewriteRequest:
    return RewriteRequest(prompt="A paper kite climbs.", duration_seconds=6)


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
