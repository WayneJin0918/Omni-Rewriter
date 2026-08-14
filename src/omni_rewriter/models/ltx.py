"""LTX-2.5 video PE profile (public cinematographer-paragraph dialect)."""

from __future__ import annotations

import json
import re
from decimal import Decimal
from enum import StrEnum
from typing import Mapping, Sequence

from pydantic import Field, field_validator, model_validator

from .common import MediaType, StrictModel, TaskType

LTX_MAX_WORDS = 200
LTX_SUPPORTED_TASKS = frozenset(
    {TaskType.T2VA, TaskType.I2VA, TaskType.FL2VA, TaskType.L2VA, TaskType.REF2VA}
)
_WORD_RE = re.compile(r"[\u4e00-\u9fff]|[A-Za-z0-9']+")
_NEWLINE_RE = re.compile(r"[\r\n]")
# Duration, resolution, and foreign PE tokens stay out of the LTX paragraph body.
# Official LTX-2 prompting: one flowing paragraph; generate params are CLI flags.
_FORBIDDEN_BODY_RE = re.compile(
    r"duration_seconds|num[-_ ]?frames|\[Shot\s+\d+\]|"
    r"@Image\s*\d+|@Video\s*\d+|@Audio\s*\d+|"
    r"<\|media:\d+\|>|<Picture\s+\d+>|<Subject\s+\d+>|"
    r"\b\d{3,4}\s*[x×]\s*\d{3,4}\b|"
    r"\b(?:16:9|9:16|4:3|21:9|3:2|1:1)\b",
    re.IGNORECASE,
)


class LTXRenderMode(StrEnum):
    """paragraph = official single-flow prompt; json = schema dump."""

    PARAGRAPH = "paragraph"
    JSON = "json"


class LTXRewrite(StrictModel):
    """Validated LTX-2.5 PE that renders to one cinematographer paragraph."""

    task: TaskType
    profile: str = "ltx"
    duration_seconds: Decimal = Field(gt=0)
    action: str = Field(min_length=1, max_length=2_000)
    movements: str = Field(min_length=1, max_length=2_000)
    appearance: str = Field(min_length=1, max_length=2_000)
    environment: str = Field(min_length=1, max_length=2_000)
    camera: str = Field(min_length=1, max_length=2_000)
    lighting: str = Field(min_length=1, max_length=2_000)
    audio: str | None = Field(default=None, max_length=2_000)
    changes: str | None = Field(default=None, max_length=2_000)
    generate_audio: bool = True

    @field_validator("task")
    @classmethod
    def require_supported_task(cls, value: TaskType) -> TaskType:
        if value not in LTX_SUPPORTED_TASKS:
            raise ValueError("LTXRewrite.task must be t2va, i2va, fl2va, l2va, or ref2va")
        return value

    @field_validator("profile")
    @classmethod
    def require_ltx_profile(cls, value: str) -> str:
        if value.strip().lower() != "ltx":
            raise ValueError("profile must be 'ltx'")
        return "ltx"

    @field_validator(
        "action",
        "movements",
        "appearance",
        "environment",
        "camera",
        "lighting",
    )
    @classmethod
    def require_single_line(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be empty")
        if _NEWLINE_RE.search(stripped):
            raise ValueError("LTX PE fields must be a single line (no newlines)")
        _reject_forbidden_markers(stripped)
        return stripped

    @field_validator("audio", "changes")
    @classmethod
    def optional_single_line(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            return None
        if _NEWLINE_RE.search(stripped):
            raise ValueError("LTX PE fields must be a single line (no newlines)")
        _reject_forbidden_markers(stripped)
        return stripped

    @model_validator(mode="after")
    def require_audio_when_enabled(self) -> "LTXRewrite":
        if self.generate_audio and not self.audio:
            raise ValueError("audio is required when generate_audio is true")
        paragraph = self.render_paragraph()
        words = count_ltx_words(paragraph)
        if words > LTX_MAX_WORDS:
            raise ValueError(
                f"rendered LTX paragraph must stay within {LTX_MAX_WORDS} words (got {words})"
            )
        return self

    def render_paragraph(self) -> str:
        """Official LTX-2 dialect: one flowing chronological paragraph."""

        parts = [
            self.action,
            self.movements,
            self.appearance,
            self.environment,
            self.camera,
            self.lighting,
        ]
        if self.changes:
            parts.append(self.changes)
        if self.generate_audio and self.audio:
            parts.append(self.audio)
        return " ".join(_ensure_sentence(part) for part in parts)

    def render_json(self) -> str:
        return json.dumps(self.model_dump(mode="json"), ensure_ascii=False, indent=2)

    def render(self) -> str:
        return self.render_paragraph()


def render_ltx_output(
    output: LTXRewrite,
    metadata: Mapping[str, str] | None = None,
) -> str:
    """Render using request metadata (`ltx_render`)."""

    meta = metadata or {}
    mode_raw = meta.get("ltx_render", LTXRenderMode.PARAGRAPH.value).strip().lower()
    try:
        mode = LTXRenderMode(mode_raw or LTXRenderMode.PARAGRAPH.value)
    except ValueError as exc:
        raise ValueError("metadata.ltx_render must be 'paragraph' or 'json'") from exc
    if mode is LTXRenderMode.JSON:
        return output.render_json()
    return output.render_paragraph()


def validate_ltx_against_request(
    output: LTXRewrite,
    *,
    media_count: int,
    task: TaskType,
    duration_seconds: Decimal | None,
    media_types: Sequence[MediaType] | None = None,
) -> None:
    """Cross-check LTX PE against the originating RewriteRequest."""

    if output.task is not task:
        raise ValueError(f"task must exactly match the request ({task.value})")
    if duration_seconds is None:
        raise ValueError("duration_seconds is required for LTX video PE")
    if output.duration_seconds != duration_seconds:
        raise ValueError(f"duration_seconds must exactly match the request ({duration_seconds})")

    types = list(media_types) if media_types is not None else []
    if media_types is not None and len(types) != media_count:
        raise ValueError("media_types length must match media_count")
    image_count = sum(item is MediaType.IMAGE for item in types) if types else 0
    if not types:
        image_count = media_count

    if task is TaskType.T2VA:
        if media_count != 0:
            raise ValueError("t2va LTX PE must not include media")
        return
    if task is TaskType.I2VA and image_count != 1:
        raise ValueError("i2va LTX PE requires exactly one image")
    if task is TaskType.L2VA and image_count != 1:
        raise ValueError("l2va LTX PE requires exactly one image")
    if task is TaskType.FL2VA and image_count != 2:
        raise ValueError("fl2va LTX PE requires exactly two images")
    if task is TaskType.REF2VA and image_count < 1:
        raise ValueError("ref2va LTX PE requires at least one image")


def count_ltx_words(text: str) -> int:
    """Count Latin tokens and CJK characters (official guide: stay within 200 words)."""

    return len(_WORD_RE.findall(text))


def frames_for_duration(duration_seconds: Decimal, frame_rate: float) -> int:
    """Map duration to official `num_frames = 8 * k + 1` at the given fps."""

    if frame_rate <= 0:
        raise ValueError("frame_rate must be positive")
    raw = max(1, int(round(float(duration_seconds) * frame_rate)))
    return max(1, (raw // 8) * 8 + 1)


def _ensure_sentence(text: str) -> str:
    stripped = text.strip()
    if stripped[-1] in ".!?。！？":
        return stripped
    return f"{stripped}."


def _reject_forbidden_markers(text: str) -> None:
    match = _FORBIDDEN_BODY_RE.search(text)
    if match:
        raise ValueError(
            "LTX paragraph must not include duration, resolution, aspect ratio, "
            f"or foreign PE tokens (found {match.group(0)!r})"
        )
