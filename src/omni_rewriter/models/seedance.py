"""Seedance video PE profile (sanitized public dialect; expand only)."""

from __future__ import annotations

import json
import re
from decimal import Decimal
from enum import StrEnum
from typing import Any, Mapping

from pydantic import Field, field_validator, model_validator

from .common import StrictModel, TaskType

PUBLIC_VIDEO_REF_RE = re.compile(
    r"(?:@Video(?P<at>[1-9]\d*)|\[Video(?P<bracket>[1-9]\d*)\])",
    re.IGNORECASE,
)
OMNI_MEDIA_REF_RE = re.compile(r"<\|media:(?P<index>[1-9]\d*)\|>")
SUBJECT_TOKEN_RE = re.compile(r"<(?:主体|Subject)\s*(?P<index>[1-9]\d*)>")


class VideoPEProfile(StrEnum):
    """Video PE dialect selector (default remains H3 when unset)."""

    H3 = "h3"
    SEEDANCE = "seedance"


class SeedanceRenderMode(StrEnum):
    NATURAL = "natural"
    JSON = "json"


class SeedanceRefStyle(StrEnum):
    PUBLIC = "public"
    OMNI = "omni"


class SeedanceSubject(StrictModel):
    """One subject appearance (and optional voice) used in the PE body."""

    id: str = Field(min_length=1, max_length=64)
    media_index: int | None = Field(default=None, ge=1, le=32)
    appearance: str = Field(min_length=1, max_length=4_000)
    voice: str | None = Field(default=None, max_length=2_000)

    @field_validator("id", "appearance")
    @classmethod
    def strip_required(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be empty")
        return stripped

    @field_validator("voice")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class SeedanceRewrite(StrictModel):
    """Validated Seedance-oriented video PE (natural or JSON render)."""

    task: TaskType
    profile: str = "seedance"
    duration_seconds: Decimal = Field(gt=0)
    style: str = Field(min_length=1, max_length=4_000)
    summary: str = Field(min_length=1, max_length=8_000)
    static_description: str = Field(min_length=1, max_length=12_000)
    dynamic_description: str = Field(min_length=1, max_length=12_000)
    subjects: list[SeedanceSubject] = Field(default_factory=list, max_length=32)
    instruction: str = Field(min_length=1, max_length=40_000)
    non_diegetic_music: str | None = Field(default=None, max_length=4_000)
    generate_audio: bool = True

    @field_validator("task")
    @classmethod
    def require_supported_task(cls, value: TaskType) -> TaskType:
        if value not in {TaskType.T2VA, TaskType.REF2VA}:
            raise ValueError("SeedanceRewrite.task must be t2va or ref2va")
        return value

    @field_validator("profile")
    @classmethod
    def require_seedance_profile(cls, value: str) -> str:
        if value.strip().lower() != "seedance":
            raise ValueError("profile must be 'seedance'")
        return "seedance"

    @field_validator(
        "style",
        "summary",
        "static_description",
        "dynamic_description",
        "instruction",
    )
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be empty")
        return stripped

    @field_validator("non_diegetic_music")
    @classmethod
    def optional_music(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def subjects_match_task(self) -> "SeedanceRewrite":
        if self.task is TaskType.REF2VA and not self.subjects:
            raise ValueError("ref2va Seedance rewrites require at least one subject")
        return self

    def media_indices_in_text(self) -> set[int]:
        found: set[int] = set()
        for match in PUBLIC_VIDEO_REF_RE.finditer(self.instruction):
            token = match.group("at") or match.group("bracket")
            if token:
                found.add(int(token))
        for match in OMNI_MEDIA_REF_RE.finditer(self.instruction):
            found.add(int(match.group("index")))
        for subject in self.subjects:
            if subject.media_index is not None:
                found.add(subject.media_index)
        return found

    def render_natural(self, *, ref_style: str = "public") -> str:
        """Fused execute-model text (style / summary / static / dynamic + instruction)."""

        style = SeedanceRefStyle(ref_style) if ref_style else SeedanceRefStyle.PUBLIC
        instruction = _rewrite_ref_tokens(self.instruction, style)
        blocks = [
            ("风格特点", self.style),
            ("内容总结", self.summary),
            ("静态描述", self.static_description),
            ("动态描述", self.dynamic_description),
        ]
        lines = [f"{title}：{body}" for title, body in blocks]
        if self.subjects:
            subject_lines = []
            for subject in self.subjects:
                label = subject.id
                media = f" (media {subject.media_index})" if subject.media_index is not None else ""
                voice = f"；voice: {subject.voice}" if subject.voice else ""
                subject_lines.append(f"- {label}{media}: {subject.appearance}{voice}")
            lines.append("主体：\n" + "\n".join(subject_lines))
        lines.append(f"生动指令：{instruction}")
        if self.non_diegetic_music:
            lines.append(f"非叙事音乐：{self.non_diegetic_music}")
        lines.append(f"generate_audio：{'true' if self.generate_audio else 'false'}")
        lines.append(f"duration_seconds：{self.duration_seconds}")
        return "\n\n".join(lines)

    def render_json(self) -> str:
        return json.dumps(self.model_dump(mode="json"), ensure_ascii=False, indent=2)

    def render(self) -> str:
        """Default community render: natural text with public @VideoN tokens."""

        return self.render_natural(ref_style=SeedanceRefStyle.PUBLIC.value)


def render_seedance_output(
    output: SeedanceRewrite,
    metadata: Mapping[str, str] | None = None,
) -> str:
    """Render using request metadata (`seedance_render`, `seedance_ref_style`)."""

    meta = metadata or {}
    mode_raw = meta.get("seedance_render", SeedanceRenderMode.NATURAL.value).strip().lower()
    style_raw = meta.get("seedance_ref_style", SeedanceRefStyle.PUBLIC.value).strip().lower()
    try:
        mode = SeedanceRenderMode(mode_raw or SeedanceRenderMode.NATURAL.value)
    except ValueError as exc:
        raise ValueError("metadata.seedance_render must be 'natural' or 'json'") from exc
    try:
        ref_style = SeedanceRefStyle(style_raw or SeedanceRefStyle.PUBLIC.value)
    except ValueError as exc:
        raise ValueError("metadata.seedance_ref_style must be 'public' or 'omni'") from exc
    if mode is SeedanceRenderMode.JSON:
        return output.render_json()
    return output.render_natural(ref_style=ref_style.value)


def validate_seedance_against_request(
    output: SeedanceRewrite,
    *,
    media_count: int,
    task: TaskType,
    duration_seconds: Decimal | None,
) -> None:
    """Cross-check Seedance PE against the originating RewriteRequest."""

    if output.task is not task:
        raise ValueError(f"task must exactly match the request ({task.value})")
    if duration_seconds is None:
        raise ValueError("duration_seconds is required for Seedance video PE")
    if output.duration_seconds != duration_seconds:
        raise ValueError(f"duration_seconds must exactly match the request ({duration_seconds})")
    for index in sorted(output.media_indices_in_text()):
        if index < 1 or index > media_count:
            raise ValueError(
                f"media reference index {index} is out of range (media count={media_count})"
            )
    if task is TaskType.T2VA and media_count == 0 and output.media_indices_in_text():
        raise ValueError("t2va Seedance instruction must not reference media indices")


def _rewrite_ref_tokens(text: str, style: SeedanceRefStyle) -> str:
    if style is SeedanceRefStyle.PUBLIC:
        return OMNI_MEDIA_REF_RE.sub(lambda match: f"@Video{match.group('index')}", text)

    def to_omni(match: re.Match[str]) -> str:
        token = match.group("at") or match.group("bracket")
        return f"<|media:{token}|>"

    return PUBLIC_VIDEO_REF_RE.sub(to_omni, text)


def seedance_fixture_forbidden_markers() -> tuple[str, ...]:
    """Markers that must never appear in checked-in Seedance fixtures."""

    return (
        "hdfs://",
        "[redacted]",
        "[redacted]",
        "uttid",
        "caption_version",
    )


def assert_sanitized_seedance_payload(payload: Any) -> None:
    """Raise ValueError if a fixture/doc payload looks like a private dump."""

    blob = json.dumps(payload, ensure_ascii=False).lower()
    for marker in seedance_fixture_forbidden_markers():
        if marker.lower() in blob:
            raise ValueError(f"Seedance fixture contains forbidden marker {marker!r}")
