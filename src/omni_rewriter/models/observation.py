"""VideoObservation: timestamped facts from a local clip, not PE and not generate."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from pydantic import Field, field_validator, model_validator

from .common import StrictModel

TIMECODE_RE = re.compile(r"^(?P<minutes>\d{2}):(?P<seconds>\d{2}\.\d{3})$")

# Longer H3 camera names first so "Arc Shot" wins over a later substring check.
H3_CAMERA_TYPES: tuple[str, ...] = (
    "Tracking Shot",
    "Arc Shot",
    "Push In",
    "Pull Out",
    "Pedestal",
    "Static",
    "Shake",
    "Truck",
    "Tilt",
    "Zoom",
    "Roll",
    "Pan",
    "POV",
)

_CAMERA_HINT = " / ".join(H3_CAMERA_TYPES)
_SPEAKER_RE = re.compile(r"^S([1-9]\d*)$")


def parse_timecode(value: str) -> Decimal:
    """Parse H3 ``MM:SS.mmm`` into seconds."""

    match = TIMECODE_RE.fullmatch(value.strip())
    if match is None:
        raise ValueError("timecode must be MM:SS.mmm")
    seconds = Decimal(match["seconds"])
    if seconds >= 60:
        raise ValueError("timecode seconds must be less than 60")
    return Decimal(match["minutes"]) * 60 + seconds


def format_timecode(seconds: Decimal) -> str:
    """Render seconds as H3 ``MM:SS.mmm`` (clip window is under one hour)."""

    if seconds < 0:
        raise ValueError("timecode seconds must be non-negative")
    total_ms = int((seconds * 1000).to_integral_value())
    minutes, ms = divmod(total_ms, 60_000)
    secs, milli = divmod(ms, 1000)
    if minutes > 99:
        raise ValueError("timecode exceeds MM:SS.mmm")
    return f"{minutes:02d}:{secs:02d}.{milli:03d}"


def coerce_timecode(value: object) -> str:
    """Accept ``MM:SS.mmm`` or a seconds number from a vision Writer."""

    if isinstance(value, bool):
        raise ValueError("timecode must be MM:SS.mmm")
    if isinstance(value, str):
        compact = value.strip()
        if TIMECODE_RE.fullmatch(compact):
            parse_timecode(compact)
            return compact
        try:
            seconds = Decimal(compact)
        except InvalidOperation as exc:
            raise ValueError("timecode must be MM:SS.mmm") from exc
        return format_timecode(seconds)
    if isinstance(value, (int, float, Decimal)):
        return format_timecode(Decimal(str(value)))
    raise ValueError("timecode must be MM:SS.mmm")


def camera_uses_h3_type(value: str) -> bool:
    """True when the camera line names a public H3 motion type."""

    compact = value.strip()
    padded = f" {compact} "
    for name in H3_CAMERA_TYPES:
        if compact == name or compact.startswith(f"{name},") or compact.startswith(f"{name} "):
            return True
        if f" {name} " in padded or f" {name}," in padded:
            return True
    return False


class ShotObservation(StrictModel):
    """One observed shot with probe-bounded timecodes."""

    index: int = Field(ge=1)
    start: str
    end: str
    visual_job: str = Field(min_length=1)
    camera: str = Field(min_length=1)
    on_screen_state: str = Field(min_length=1)

    @field_validator("start", "end", mode="before")
    @classmethod
    def validate_timecode(cls, value: object) -> str:
        return coerce_timecode(value)

    @field_validator("camera")
    @classmethod
    def validate_camera(cls, value: str) -> str:
        if not camera_uses_h3_type(value):
            raise ValueError(f"camera must use an H3 type ({_CAMERA_HINT})")
        return value

    @model_validator(mode="after")
    def validate_window(self) -> "ShotObservation":
        if parse_timecode(self.end) < parse_timecode(self.start):
            raise ValueError("shot end must be at or after start")
        return self


class DialogueObservation(StrictModel):
    """A spoken line located on the timeline."""

    at: str
    speaker: str = Field(min_length=1)
    language: str = Field(min_length=1)
    text: str = Field(min_length=1)
    inferred: bool = True

    @field_validator("at", mode="before")
    @classmethod
    def validate_at(cls, value: object) -> str:
        return coerce_timecode(value)

    @field_validator("speaker")
    @classmethod
    def validate_speaker(cls, value: str) -> str:
        if _SPEAKER_RE.fullmatch(value) is None:
            raise ValueError("speaker must be S1, S2, …")
        return value


class VideoObservation(StrictModel):
    """Grounded clip reading. Writer must not invent duration_seconds."""

    duration_seconds: Decimal = Field(gt=0)
    invariants: list[str] = Field(min_length=1)
    shots: list[ShotObservation] = Field(min_length=1)
    dialogue: list[DialogueObservation] = Field(default_factory=list)
    soundscape: str = Field(min_length=1)
    music: str = Field(min_length=1)
    uncertainties: list[str] = Field(default_factory=list)

    @field_validator("invariants")
    @classmethod
    def validate_invariants(cls, value: list[str]) -> list[str]:
        if any(not item.strip() for item in value):
            raise ValueError("invariants must not contain blank strings")
        return value

    @model_validator(mode="after")
    def validate_timeline(self) -> "VideoObservation":
        duration = self.duration_seconds
        indices = [shot.index for shot in self.shots]
        if indices != list(range(1, len(self.shots) + 1)):
            raise ValueError("shot index must start at 1 and be sequential")
        previous_end = Decimal("-1")
        for shot in self.shots:
            start = parse_timecode(shot.start)
            end = parse_timecode(shot.end)
            if start >= duration or end > duration:
                raise ValueError("shot times must fall within duration_seconds")
            if start < previous_end:
                raise ValueError("shot windows must not go backwards")
            previous_end = end
        speakers: list[int] = []
        for line in self.dialogue:
            at = parse_timecode(line.at)
            if at >= duration:
                raise ValueError("dialogue timecodes must fall before duration_seconds")
            matched = _SPEAKER_RE.fullmatch(line.speaker)
            if matched is None:
                raise ValueError("speaker must be S1, S2, …")
            speakers.append(int(matched.group(1)))
        if speakers:
            unique = sorted(set(speakers))
            if unique != list(range(1, max(unique) + 1)):
                raise ValueError("dialogue speakers must be contiguous from S1")
        if "<d>" in self.soundscape or "<d>" in self.music:
            raise ValueError("dialogue belongs in dialogue[], not soundscape or music")
        return self


def bind_probe_duration(observation: VideoObservation, duration: Decimal) -> VideoObservation:
    """Force ffprobe duration and re-validate shot/dialogue bounds."""

    payload = observation.model_dump()
    payload["duration_seconds"] = duration
    return VideoObservation.model_validate(payload)
