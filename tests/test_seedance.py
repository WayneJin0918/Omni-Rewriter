"""Seedance video PE schema, renders, sanitization, and agent wiring."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from omni_rewriter.agent import RewriteAgent
from omni_rewriter.backends import ScriptedBackend
from omni_rewriter.models import (
    MediaReference,
    MediaRole,
    MediaType,
    RewriteRequest,
    SeedanceRewrite,
    TaskType,
    render_seedance_output,
)
from omni_rewriter.models.seedance import (
    assert_sanitized_seedance_payload,
    seedance_fixture_forbidden_markers,
    validate_seedance_against_request,
)
from omni_rewriter.service import render_output, validate_output

FIXTURES = Path(__file__).parent / "fixtures" / "seedance"


def _load(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_seedance_t2va_schema_and_natural_render() -> None:
    envelope = _load("t2va_kitchen.json")
    output, request = validate_output(envelope)
    assert isinstance(output, SeedanceRewrite)
    assert request is not None
    text = render_output(output, request)
    assert "风格特点：" in text
    assert "How does the soup taste today?" in text
    assert "duration_seconds：8" in text


def test_seedance_ref2va_json_render_and_media_indices() -> None:
    envelope = _load("ref2va_interview.json")
    output, request = validate_output(envelope)
    assert isinstance(output, SeedanceRewrite)
    assert request is not None
    rendered = render_seedance_output(output, request.metadata)
    payload = json.loads(rendered)
    assert payload["profile"] == "seedance"
    assert payload["subjects"][0]["media_index"] == 1
    assert "@Video1" in payload["instruction"]


def test_seedance_ref_style_omni_rewrites_tokens() -> None:
    envelope = _load("ref2va_interview.json")
    output, _ = validate_output(envelope)
    assert isinstance(output, SeedanceRewrite)
    text = output.render_natural(ref_style="omni")
    assert "Preserve <|media:1|> and <|media:2|>" in text


def test_seedance_rejects_dangling_media_index() -> None:
    envelope = _load("t2va_kitchen.json")
    output = SeedanceRewrite.model_validate(envelope["output"])
    broken = output.model_copy(
        update={"instruction": output.instruction + " See @Video1 for plating."}
    )
    with pytest.raises(ValueError, match="out of range"):
        validate_seedance_against_request(
            broken,
            media_count=0,
            task=TaskType.T2VA,
            duration_seconds=Decimal("8"),
        )


def test_seedance_ref2va_requires_subjects() -> None:
    with pytest.raises(ValidationError, match="at least one subject"):
        SeedanceRewrite(
            task=TaskType.REF2VA,
            duration_seconds=Decimal("6"),
            style="style",
            summary="summary",
            static_description="static",
            dynamic_description="dynamic",
            subjects=[],
            instruction="Keep @Video1 identity.",
        )


def test_seedance_fixtures_are_sanitized() -> None:
    markers = seedance_fixture_forbidden_markers()
    for path in FIXTURES.glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert_sanitized_seedance_payload(payload)
        blob = path.read_text(encoding="utf-8").lower()
        for marker in markers:
            assert marker.lower() not in blob


@pytest.mark.asyncio
async def test_agent_seedance_t2va(
    analysis_output: dict[str, object],
) -> None:
    envelope = _load("t2va_kitchen.json")
    backend = ScriptedBackend([json.dumps(analysis_output), json.dumps(envelope["output"])])
    result = await RewriteAgent(backend).run(RewriteRequest.model_validate(envelope["request"]))
    assert isinstance(result.output, SeedanceRewrite)
    assert "风格特点" in result.output.render()


@pytest.mark.asyncio
async def test_agent_seedance_ref2va(
    analysis_output: dict[str, object],
) -> None:
    envelope = _load("ref2va_interview.json")
    output = dict(envelope["output"])
    # Agent path uses synthetic in-memory refs (no remote download).
    request = RewriteRequest(
        prompt=str(envelope["request"]["prompt"]),
        duration_seconds=Decimal("10"),
        task=TaskType.REF2VA,
        media=[
            MediaReference(
                media_type=MediaType.IMAGE,
                role=MediaRole.REFERENCE,
                uri=(
                    "data:image/png;base64,"
                    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
                ),
                name="host_ref",
            ),
            MediaReference(
                media_type=MediaType.IMAGE,
                role=MediaRole.REFERENCE,
                uri=(
                    "data:image/png;base64,"
                    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
                ),
                name="guest_ref",
            ),
        ],
        metadata={
            "video_pe_profile": "seedance",
            "seedance_render": "natural",
            "seedance_ref_style": "public",
        },
    )
    backend = ScriptedBackend([json.dumps(analysis_output), json.dumps(output)])
    result = await RewriteAgent(backend).run(request)
    assert isinstance(result.output, SeedanceRewrite)
    assert result.output.subjects[0].media_index == 1
