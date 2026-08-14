"""LTX-2.5 video PE schema, paragraph render, and agent wiring."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from omni_rewriter.agent import RewriteAgent
from omni_rewriter.backends import ScriptedBackend
from omni_rewriter.models import (
    LTXRewrite,
    MediaReference,
    MediaRole,
    MediaType,
    RewriteRequest,
    TaskType,
    render_ltx_output,
)
from omni_rewriter.models.ltx import (
    count_ltx_words,
    frames_for_duration,
    validate_ltx_against_request,
)
from omni_rewriter.service import render_output, validate_output

FIXTURES = Path(__file__).parent / "fixtures" / "ltx"


def _load(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_ltx_t2va_schema_and_paragraph_render() -> None:
    envelope = _load("t2va_workshop.json")
    output, request = validate_output(envelope)
    assert isinstance(output, LTXRewrite)
    assert request is not None
    text = render_output(output, request)
    assert text.startswith("A potter throws")
    assert "\n" not in text
    assert "duration_seconds" not in text
    assert "[Shot" not in text
    assert count_ltx_words(text) <= 200
    assert "wheel hums" in text


def test_ltx_json_render() -> None:
    envelope = _load("t2va_workshop.json")
    output = LTXRewrite.model_validate(envelope["output"])
    payload = json.loads(render_ltx_output(output, {"ltx_render": "json"}))
    assert payload["profile"] == "ltx"
    assert payload["task"] == "t2va"


def test_ltx_i2va_requires_one_image() -> None:
    envelope = _load("i2va_portrait.json")
    output, request = validate_output(envelope)
    assert isinstance(output, LTXRewrite)
    assert request is not None
    text = render_output(output, request)
    assert "@Image" not in text
    assert "reference still" in text


def test_ltx_rejects_duration_in_body() -> None:
    envelope = _load("t2va_workshop.json")
    payload = dict(envelope["output"])
    payload["action"] = "A 5 duration_seconds clip of a potter"
    with pytest.raises(ValidationError, match="duration"):
        LTXRewrite.model_validate(payload)


def test_ltx_rejects_overlong_paragraph() -> None:
    envelope = _load("t2va_workshop.json")
    payload = dict(envelope["output"])
    payload["movements"] = " ".join(["turns"] * 200)
    with pytest.raises(ValidationError, match="200 words"):
        LTXRewrite.model_validate(payload)


def test_ltx_t2va_rejects_media() -> None:
    envelope = _load("t2va_workshop.json")
    output = LTXRewrite.model_validate(envelope["output"])
    with pytest.raises(ValueError, match="must not include media"):
        validate_ltx_against_request(
            output,
            media_count=1,
            task=TaskType.T2VA,
            duration_seconds=Decimal("5"),
            media_types=[MediaType.IMAGE],
        )


def test_ltx_frames_for_duration() -> None:
    assert frames_for_duration(Decimal("5"), 24.0) == 121
    assert frames_for_duration(Decimal("8"), 24.0) == 193


@pytest.mark.asyncio
async def test_agent_ltx_t2va(analysis_output: dict[str, object]) -> None:
    envelope = _load("t2va_workshop.json")
    backend = ScriptedBackend([json.dumps(analysis_output), json.dumps(envelope["output"])])
    result = await RewriteAgent(backend).run(RewriteRequest.model_validate(envelope["request"]))
    assert isinstance(result.output, LTXRewrite)
    assert "A potter throws" in result.output.render()


@pytest.mark.asyncio
async def test_agent_ltx_i2va(analysis_output: dict[str, object]) -> None:
    envelope = _load("i2va_portrait.json")
    request = RewriteRequest(
        prompt=str(envelope["request"]["prompt"]),
        duration_seconds=Decimal("5"),
        task=TaskType.I2VA,
        media=[
            MediaReference(
                media_type=MediaType.IMAGE,
                role=MediaRole.FIRST_FRAME,
                uri=(
                    "data:image/png;base64,"
                    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
                ),
                name="portrait",
            )
        ],
        metadata={"video_pe_profile": "ltx"},
    )
    backend = ScriptedBackend([json.dumps(analysis_output), json.dumps(envelope["output"])])
    result = await RewriteAgent(backend).run(request)
    assert isinstance(result.output, LTXRewrite)
    assert result.output.task is TaskType.I2VA
