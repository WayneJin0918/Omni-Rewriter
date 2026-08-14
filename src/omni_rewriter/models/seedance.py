"""Seedance video PE profile (sanitized public dialect; expand only)."""

from __future__ import annotations

import json
import re
from collections import Counter
from decimal import Decimal
from enum import StrEnum
from typing import Any, Mapping, Sequence

from pydantic import Field, field_validator, model_validator

from .common import MediaType, StrictModel, TaskType

# Public Seedance 2.5 tokens are type-local and usually spaced (`@Image 1`).
# Compact `@Video1` / `[Video1]` remain accepted for older public API habits.
PUBLIC_TYPED_REF_RE = re.compile(
    r"(?:@(?P<kind_at>Image|Video|Audio)\s*(?P<at>[1-9]\d*)|"
    r"\[(?P<kind_bracket>Image|Video|Audio)\s*(?P<bracket>[1-9]\d*)\])",
    re.IGNORECASE,
)
PUBLIC_VIDEO_REF_RE = re.compile(
    r"(?:@Video(?P<at>[1-9]\d*)|\[Video(?P<bracket>[1-9]\d*)\])",
    re.IGNORECASE,
)
OMNI_MEDIA_REF_RE = re.compile(r"<\|media:(?P<index>[1-9]\d*)\|>")
SUBJECT_TOKEN_RE = re.compile(r"<(?:主体|Subject)\s*(?P<index>[1-9]\d*)>")

_SEEDANCE_IMAGE_LIMIT = 30
_SEEDANCE_VIDEO_LIMIT = 10
_SEEDANCE_AUDIO_LIMIT = 10
_SEEDANCE_TOTAL_MEDIA_LIMIT = 50


class VideoPEProfile(StrEnum):
    """Video PE dialect selector (default remains H3 when unset)."""

    H3 = "h3"
    SEEDANCE = "seedance"
    LTX = "ltx"


class SeedanceRenderMode(StrEnum):
    """natural = public Seedance 2.5 template; fused = legacy labeled blocks; json = schema."""

    NATURAL = "natural"
    FUSED = "fused"
    JSON = "json"


class SeedanceRefStyle(StrEnum):
    PUBLIC = "public"
    OMNI = "omni"


class SeedanceMediaKind(StrEnum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class SeedanceReferenceRole(StrictModel):
    """One activated reference material with an explicit inherit/exclude contract."""

    media_type: SeedanceMediaKind
    index: int = Field(ge=1, le=_SEEDANCE_IMAGE_LIMIT)
    defines: str = Field(min_length=1, max_length=4_000)
    exclude: str | None = Field(default=None, max_length=2_000)

    @field_validator("defines")
    @classmethod
    def strip_defines(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be empty")
        return stripped

    @field_validator("exclude")
    @classmethod
    def strip_exclude(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def index_within_type_cap(self) -> "SeedanceReferenceRole":
        limit = {
            SeedanceMediaKind.IMAGE: _SEEDANCE_IMAGE_LIMIT,
            SeedanceMediaKind.VIDEO: _SEEDANCE_VIDEO_LIMIT,
            SeedanceMediaKind.AUDIO: _SEEDANCE_AUDIO_LIMIT,
        }[self.media_type]
        if self.index > limit:
            raise ValueError(
                f"{self.media_type.value} reference index {self.index} exceeds public cap {limit}"
            )
        return self

    def public_token(self) -> str:
        label = {
            SeedanceMediaKind.IMAGE: "Image",
            SeedanceMediaKind.VIDEO: "Video",
            SeedanceMediaKind.AUDIO: "Audio",
        }[self.media_type]
        return f"@{label} {self.index}"


class SeedanceStage(StrictModel):
    """One beat with a single primary state change and an observable end state."""

    time_range: str | None = Field(default=None, max_length=64)
    event: str = Field(min_length=1, max_length=8_000)
    end_state: str = Field(min_length=1, max_length=4_000)

    @field_validator("event", "end_state")
    @classmethod
    def strip_required(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be empty")
        return stripped

    @field_validator("time_range")
    @classmethod
    def strip_time_range(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class SeedanceSubject(StrictModel):
    """One subject appearance (and optional voice) used in the PE body."""

    id: str = Field(min_length=1, max_length=64)
    media_type: SeedanceMediaKind | None = None
    media_index: int | None = Field(default=None, ge=1, le=_SEEDANCE_IMAGE_LIMIT)
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

    @model_validator(mode="after")
    def typed_index_requires_kind(self) -> "SeedanceSubject":
        if self.media_type is not None and self.media_index is None:
            raise ValueError("media_index is required when media_type is set")
        if self.media_type is not None and self.media_index is not None:
            limit = {
                SeedanceMediaKind.IMAGE: _SEEDANCE_IMAGE_LIMIT,
                SeedanceMediaKind.VIDEO: _SEEDANCE_VIDEO_LIMIT,
                SeedanceMediaKind.AUDIO: _SEEDANCE_AUDIO_LIMIT,
            }[self.media_type]
            if self.media_index > limit:
                raise ValueError(
                    f"{self.media_type.value} media_index {self.media_index} "
                    f"exceeds public cap {limit}"
                )
        return self


class SeedanceRewrite(StrictModel):
    """Validated Seedance-oriented video PE (natural, fused, or JSON render)."""

    task: TaskType
    profile: str = "seedance"
    duration_seconds: Decimal = Field(gt=0)
    style: str = Field(min_length=1, max_length=4_000)
    summary: str = Field(min_length=1, max_length=8_000)
    static_description: str = Field(min_length=1, max_length=12_000)
    dynamic_description: str = Field(min_length=1, max_length=12_000)
    subjects: list[SeedanceSubject] = Field(default_factory=list, max_length=32)
    reference_roles: list[SeedanceReferenceRole] = Field(default_factory=list, max_length=50)
    stages: list[SeedanceStage] = Field(default_factory=list, max_length=32)
    preserve: list[str] = Field(default_factory=list, max_length=32)
    unused_materials: list[str] = Field(default_factory=list, max_length=50)
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

    @field_validator("preserve", "unused_materials")
    @classmethod
    def strip_string_list(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in values:
            stripped = item.strip()
            if stripped:
                cleaned.append(stripped)
        return cleaned

    @model_validator(mode="after")
    def subjects_match_task(self) -> "SeedanceRewrite":
        if self.task is TaskType.REF2VA and not self.subjects and not self.reference_roles:
            raise ValueError(
                "ref2va Seedance rewrites require at least one subject or reference_role"
            )
        return self

    def typed_refs_in_text(self) -> set[tuple[SeedanceMediaKind, int]]:
        found: set[tuple[SeedanceMediaKind, int]] = set()
        blobs = [self.instruction, self.static_description, self.dynamic_description, self.summary]
        blobs.extend(role.defines for role in self.reference_roles)
        blobs.extend(role.exclude for role in self.reference_roles if role.exclude)
        blobs.extend(stage.event for stage in self.stages)
        blobs.extend(stage.end_state for stage in self.stages)
        blobs.extend(self.preserve)
        blobs.extend(self.unused_materials)
        for subject in self.subjects:
            blobs.append(subject.appearance)
            if subject.voice:
                blobs.append(subject.voice)
        for blob in blobs:
            for match in PUBLIC_TYPED_REF_RE.finditer(blob):
                kind_raw = match.group("kind_at") or match.group("kind_bracket")
                token = match.group("at") or match.group("bracket")
                if kind_raw and token:
                    found.add((SeedanceMediaKind(kind_raw.lower()), int(token)))
        for role in self.reference_roles:
            found.add((role.media_type, role.index))
        for subject in self.subjects:
            if subject.media_type is not None and subject.media_index is not None:
                found.add((subject.media_type, subject.media_index))
        return found

    def flat_media_indices_in_text(self) -> set[int]:
        """Legacy / omni flat indices (`<|media:N|>` or subject.media_index without type)."""

        found: set[int] = set()
        for match in OMNI_MEDIA_REF_RE.finditer(self.instruction):
            found.add(int(match.group("index")))
        for subject in self.subjects:
            if subject.media_type is None and subject.media_index is not None:
                found.add(subject.media_index)
        return found

    def media_indices_in_text(self) -> set[int]:
        """Backward-compatible flat index set used by older callers/tests."""

        found = set(self.flat_media_indices_in_text())
        for _kind, index in self.typed_refs_in_text():
            found.add(index)
        return found

    def render_natural(self, *, ref_style: str = "public") -> str:
        """Public Seedance 2.5 submit-ready template (parameters stay out of the body)."""

        style = SeedanceRefStyle(ref_style) if ref_style else SeedanceRefStyle.PUBLIC
        instruction = _rewrite_ref_tokens(self.instruction, style)
        sections: list[str] = [f"[Generation Goal]\n{self.summary.strip()}"]

        if self.reference_roles:
            role_lines = []
            for role in self.reference_roles:
                token = role.public_token()
                if style is SeedanceRefStyle.OMNI:
                    # Omni tokens are flat; keep public typed labels in role lines unless
                    # the caller already used omni elsewhere.
                    token = role.public_token()
                line = f"{token} defines {role.defines}"
                if role.exclude:
                    line = f"{line}. Do not use {role.exclude}"
                if not line.endswith("."):
                    line += "."
                role_lines.append(line)
            sections.append("[Reference Material Roles]\n" + "\n".join(role_lines))

        if self.unused_materials:
            sections.append("[Unused Materials]\n" + "\n".join(self.unused_materials))

        if self.subjects:
            subject_lines = []
            for subject in self.subjects:
                if subject.media_type is not None and subject.media_index is not None:
                    label = {
                        SeedanceMediaKind.IMAGE: "Image",
                        SeedanceMediaKind.VIDEO: "Video",
                        SeedanceMediaKind.AUDIO: "Audio",
                    }[subject.media_type]
                    media = f" corresponds to @{label} {subject.media_index}"
                elif subject.media_index is not None:
                    media = f" (media {subject.media_index})"
                else:
                    media = ""
                voice = f" Voice: {subject.voice}." if subject.voice else ""
                subject_lines.append(f"{subject.id}{media}. {subject.appearance}{voice}")
            sections.append("[Subjects and Relationships]\n" + "\n".join(subject_lines))

        event_lines = [f"Opening state: {self.static_description}"]
        if self.stages:
            for index, stage in enumerate(self.stages, start=1):
                prefix = f"Stage {index}"
                if stage.time_range:
                    prefix = f"{prefix} ({stage.time_range})"
                event_lines.append(f"{prefix}: {stage.event} End state: {stage.end_state}")
        else:
            event_lines.append(f"Primary event: {self.dynamic_description}")
        event_lines.append(instruction)
        sections.append("[Event Script]\n" + "\n".join(event_lines))

        visual_bits = [self.style.strip()]
        if self.dynamic_description and self.stages:
            visual_bits.append(self.dynamic_description.strip())
        sections.append("[Visual Treatment]\n" + " ".join(visual_bits))

        audio_bits: list[str] = []
        if self.non_diegetic_music:
            music = self.non_diegetic_music.strip()
            if not (music.startswith("(") and music.endswith(")")):
                music = f"({music})"
            audio_bits.append(music)
        if self.generate_audio is False:
            audio_bits.append("No generated dialogue or score beyond what is written above.")
        if audio_bits:
            sections.append("[Audio]\n" + " ".join(audio_bits))

        if self.preserve:
            sections.append("[Maintain Consistency]\n" + "\n".join(self.preserve))

        body = "\n\n".join(sections)
        if style is SeedanceRefStyle.OMNI:
            return _rewrite_ref_tokens(body, SeedanceRefStyle.OMNI)
        return body

    def render_fused(self, *, ref_style: str = "public") -> str:
        """Legacy fused execute-model text (风格特点 / 内容总结 / …)."""

        style = SeedanceRefStyle(ref_style) if ref_style else SeedanceRefStyle.PUBLIC
        instruction = _rewrite_ref_tokens(self.instruction, style)
        blocks = [
            ("风格特点", self.style),
            ("内容总结", self.summary),
            ("静态描述", self.static_description),
            ("动态描述", self.dynamic_description),
        ]
        lines = [f"{title}：{body}" for title, body in blocks]
        if self.reference_roles:
            role_lines = []
            for role in self.reference_roles:
                exclude = f"；exclude: {role.exclude}" if role.exclude else ""
                role_lines.append(f"- {role.public_token()}: {role.defines}{exclude}")
            lines.append("参考角色：\n" + "\n".join(role_lines))
        if self.subjects:
            subject_lines = []
            for subject in self.subjects:
                if subject.media_type is not None and subject.media_index is not None:
                    media = f" ({subject.media_type.value} {subject.media_index})"
                elif subject.media_index is not None:
                    media = f" (media {subject.media_index})"
                else:
                    media = ""
                voice = f"；voice: {subject.voice}" if subject.voice else ""
                subject_lines.append(f"- {subject.id}{media}: {subject.appearance}{voice}")
            lines.append("主体：\n" + "\n".join(subject_lines))
        if self.stages:
            stage_lines = []
            for index, stage in enumerate(self.stages, start=1):
                timing = f" [{stage.time_range}]" if stage.time_range else ""
                stage_lines.append(f"- Stage {index}{timing}: {stage.event} → {stage.end_state}")
            lines.append("阶段：\n" + "\n".join(stage_lines))
        lines.append(f"生动指令：{instruction}")
        if self.non_diegetic_music:
            lines.append(f"非叙事音乐：{self.non_diegetic_music}")
        if self.preserve:
            lines.append("保持一致：\n" + "\n".join(f"- {item}" for item in self.preserve))
        lines.append(f"generate_audio：{'true' if self.generate_audio else 'false'}")
        lines.append(f"duration_seconds：{self.duration_seconds}")
        return "\n\n".join(lines)

    def render_json(self) -> str:
        return json.dumps(self.model_dump(mode="json"), ensure_ascii=False, indent=2)

    def render(self) -> str:
        """Default community render: public Seedance 2.5 natural template."""

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
        raise ValueError("metadata.seedance_render must be 'natural', 'fused', or 'json'") from exc
    try:
        ref_style = SeedanceRefStyle(style_raw or SeedanceRefStyle.PUBLIC.value)
    except ValueError as exc:
        raise ValueError("metadata.seedance_ref_style must be 'public' or 'omni'") from exc
    if mode is SeedanceRenderMode.JSON:
        return output.render_json()
    if mode is SeedanceRenderMode.FUSED:
        return output.render_fused(ref_style=ref_style.value)
    return output.render_natural(ref_style=ref_style.value)


def validate_seedance_against_request(
    output: SeedanceRewrite,
    *,
    media_count: int,
    task: TaskType,
    duration_seconds: Decimal | None,
    media_types: Sequence[MediaType] | None = None,
) -> None:
    """Cross-check Seedance PE against the originating RewriteRequest."""

    if output.task is not task:
        raise ValueError(f"task must exactly match the request ({task.value})")
    if duration_seconds is None:
        raise ValueError("duration_seconds is required for Seedance video PE")
    if output.duration_seconds != duration_seconds:
        raise ValueError(f"duration_seconds must exactly match the request ({duration_seconds})")

    types = list(media_types) if media_types is not None else []
    if media_types is not None and len(types) != media_count:
        raise ValueError("media_types length must match media_count")

    type_counts = Counter(types) if types else Counter()
    if types:
        if type_counts[MediaType.IMAGE] > _SEEDANCE_IMAGE_LIMIT:
            raise ValueError(
                f"Seedance public image reference cap is {_SEEDANCE_IMAGE_LIMIT} "
                f"(got {type_counts[MediaType.IMAGE]})"
            )
        if type_counts[MediaType.VIDEO] > _SEEDANCE_VIDEO_LIMIT:
            raise ValueError(
                f"Seedance public video reference cap is {_SEEDANCE_VIDEO_LIMIT} "
                f"(got {type_counts[MediaType.VIDEO]})"
            )
        if type_counts[MediaType.AUDIO] > _SEEDANCE_AUDIO_LIMIT:
            raise ValueError(
                f"Seedance public audio reference cap is {_SEEDANCE_AUDIO_LIMIT} "
                f"(got {type_counts[MediaType.AUDIO]})"
            )
        if media_count > _SEEDANCE_TOTAL_MEDIA_LIMIT:
            raise ValueError(
                f"Seedance public total reference cap is {_SEEDANCE_TOTAL_MEDIA_LIMIT} "
                f"(got {media_count})"
            )

        kind_to_media = {
            SeedanceMediaKind.IMAGE: MediaType.IMAGE,
            SeedanceMediaKind.VIDEO: MediaType.VIDEO,
            SeedanceMediaKind.AUDIO: MediaType.AUDIO,
        }
        for kind, index in sorted(
            output.typed_refs_in_text(), key=lambda item: (item[0].value, item[1])
        ):
            available = type_counts[kind_to_media[kind]]
            if index < 1 or index > available:
                raise ValueError(
                    f"{kind.value} reference index {index} is out of range "
                    f"({kind.value} count={available})"
                )
        for index in sorted(output.flat_media_indices_in_text()):
            if index < 1 or index > media_count:
                raise ValueError(
                    f"media reference index {index} is out of range (media count={media_count})"
                )
    else:
        for index in sorted(output.media_indices_in_text()):
            if index < 1 or index > media_count:
                raise ValueError(
                    f"media reference index {index} is out of range (media count={media_count})"
                )

    if (
        task is TaskType.T2VA
        and media_count == 0
        and (output.typed_refs_in_text() or output.flat_media_indices_in_text())
    ):
        raise ValueError("t2va Seedance instruction must not reference media indices")


def _rewrite_ref_tokens(text: str, style: SeedanceRefStyle) -> str:
    if style is SeedanceRefStyle.PUBLIC:
        # Normalize compact/omni forms toward spaced public tokens when possible.
        text = OMNI_MEDIA_REF_RE.sub(lambda match: f"@Video {match.group('index')}", text)

        def space_compact(match: re.Match[str]) -> str:
            kind = match.group("kind_at") or match.group("kind_bracket") or "Video"
            token = match.group("at") or match.group("bracket")
            # Preserve already-spaced tokens; rewrite compact @Video1 → @Video 1.
            raw = match.group(0)
            if " " in raw:
                return raw
            label = kind[:1].upper() + kind[1:].lower()
            return f"@{label} {token}"

        return PUBLIC_TYPED_REF_RE.sub(space_compact, text)

    def to_omni_typed(match: re.Match[str]) -> str:
        # Omni flat indices cannot encode type-local numbering; keep a stable Video-shaped
        # placeholder only for compact video tokens, otherwise leave typed public tokens.
        kind = (match.group("kind_at") or match.group("kind_bracket") or "").lower()
        token = match.group("at") or match.group("bracket")
        if kind == "video":
            return f"<|media:{token}|>"
        return match.group(0)

    text = PUBLIC_TYPED_REF_RE.sub(to_omni_typed, text)

    def to_omni_compact(match: re.Match[str]) -> str:
        token = match.group("at") or match.group("bracket")
        return f"<|media:{token}|>"

    return PUBLIC_VIDEO_REF_RE.sub(to_omni_compact, text)


def seedance_fixture_forbidden_markers() -> tuple[str, ...]:
    """Markers that must never appear in checked-in Seedance fixtures.

    Pieces are joined at runtime so vendor-private tokens are not stored as
    contiguous literals in the public tree.
    """

    return tuple(
        "".join(parts)
        for parts in (
            ("hdfs", "://"),
            ("har", "una"),
            ("byte_data", "_seed"),
            ("utt", "id"),
            ("caption", "_version"),
        )
    )


def assert_sanitized_seedance_payload(payload: Any) -> None:
    """Raise ValueError if a fixture/doc payload looks like a private dump."""

    blob = json.dumps(payload, ensure_ascii=False).lower()
    for marker in seedance_fixture_forbidden_markers():
        if marker.lower() in blob:
            raise ValueError(f"Seedance fixture contains forbidden marker {marker!r}")
