"""Deterministic ffmpeg/ffprobe evidence pack. No Writer, no PE, no generate."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any

from pydantic import Field

from ..errors import ReconstructError
from ..models.common import StrictModel
from ..models.observation import format_timecode

_DEFAULT_MAX_DURATION = Decimal("45")
_DEFAULT_STEP = Decimal("0.5")
_DEFAULT_MAX_FRAMES = 16
_DEFAULT_SHORT_SIDE = 640


class EvidencePackError(ReconstructError):
    """ffmpeg/ffprobe could not build a bounded evidence pack."""


class EvidencePackConfig(StrictModel):
    """Caps for local clip probing and keyframe extraction."""

    max_duration_seconds: Decimal = Field(default=_DEFAULT_MAX_DURATION, gt=0)
    step_seconds: Decimal = Field(default=_DEFAULT_STEP, gt=0)
    max_keyframes: int = Field(default=_DEFAULT_MAX_FRAMES, ge=2, le=32)
    short_side: int = Field(default=_DEFAULT_SHORT_SIDE, ge=256, le=768)
    jpeg_quality: int = Field(default=3, ge=2, le=8)
    extract_audio: bool = True


@dataclass(frozen=True, slots=True)
class ProbeInfo:
    duration_seconds: Decimal
    fps: float
    width: int
    height: int
    has_video: bool
    has_audio: bool


@dataclass(frozen=True, slots=True)
class Keyframe:
    index: int
    seconds: Decimal
    timecode: str
    path: Path


@dataclass(frozen=True, slots=True)
class EvidencePack:
    source: Path
    pack_dir: Path
    probe: ProbeInfo
    frames: list[Keyframe] = field(default_factory=list)
    audio_wav: Path | None = None

    def summary(self) -> dict[str, Any]:
        """JSON-safe pack metadata. Does not include JPEG bytes."""

        return {
            "source": str(self.source),
            "pack_dir": str(self.pack_dir),
            "probe": {
                "duration_seconds": str(self.probe.duration_seconds),
                "fps": self.probe.fps,
                "width": self.probe.width,
                "height": self.probe.height,
                "has_video": self.probe.has_video,
                "has_audio": self.probe.has_audio,
            },
            "frames": [
                {
                    "index": frame.index,
                    "seconds": str(frame.seconds),
                    "timecode": frame.timecode,
                    "path": str(frame.path),
                }
                for frame in self.frames
            ],
            "audio_wav": str(self.audio_wav) if self.audio_wav else None,
        }


def build_evidence_pack(
    source: Path,
    pack_dir: Path,
    config: EvidencePackConfig | None = None,
) -> EvidencePack:
    """Probe ``source`` and write downsampled JPEG keyframes (and optional wav)."""

    config = config or EvidencePackConfig()
    _require_binaries()
    clip = source.expanduser().resolve()
    if not clip.is_file():
        raise EvidencePackError(f"source is not a file: {source}")
    dest = pack_dir.expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)
    probe = probe_clip(clip)
    if not probe.has_video:
        raise EvidencePackError("source has no video stream")
    if probe.duration_seconds > config.max_duration_seconds:
        raise EvidencePackError(
            f"clip is {probe.duration_seconds}s; reconstruct v1 cap is "
            f"{config.max_duration_seconds}s"
        )
    times = _sample_times(probe.duration_seconds, config.step_seconds, config.max_keyframes)
    frames_dir = dest / "frames"
    frames_dir.mkdir(exist_ok=True)
    frames: list[Keyframe] = []
    scale = (
        f"scale='if(lt(iw,ih),{config.short_side},-2)':"
        f"'if(lt(iw,ih),-2,{config.short_side})',format=yuvj420p"
    )
    for index, seconds in enumerate(times, start=1):
        timecode = format_timecode(seconds)
        path = frames_dir / f"{index:02d}_{timecode.replace(':', '-').replace('.', '-')}.jpg"
        _run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(clip),
                "-ss",
                f"{seconds:.3f}",
                "-frames:v",
                "1",
                "-vf",
                scale,
                "-q:v",
                str(config.jpeg_quality),
                str(path),
            ]
        )
        if not path.is_file() or path.stat().st_size == 0:
            raise EvidencePackError(f"failed to extract frame at {timecode}")
        frames.append(Keyframe(index=index, seconds=seconds, timecode=timecode, path=path))
    audio_wav: Path | None = None
    if config.extract_audio and probe.has_audio:
        audio_wav = dest / "audio.wav"
        _run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(clip),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                str(audio_wav),
            ]
        )
    return EvidencePack(
        source=clip,
        pack_dir=dest,
        probe=probe,
        frames=frames,
        audio_wav=audio_wav,
    )


def probe_clip(source: Path) -> ProbeInfo:
    """Return container duration and the primary video/audio streams."""

    raw = _run(
        [
            "ffprobe",
            "-hide_banner",
            "-loglevel",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(source),
        ]
    )
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise EvidencePackError("ffprobe returned invalid JSON") from exc
    streams = payload.get("streams") or []
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    duration_raw = (payload.get("format") or {}).get("duration")
    if video is None or not duration_raw:
        raise EvidencePackError("ffprobe could not read a timed video stream")
    duration = Decimal(str(duration_raw)).quantize(Decimal("0.001"))
    fps = _fps(video.get("avg_frame_rate") or video.get("r_frame_rate") or "0/1")
    return ProbeInfo(
        duration_seconds=duration,
        fps=fps,
        width=int(video.get("width") or 0),
        height=int(video.get("height") or 0),
        has_video=True,
        has_audio=audio is not None,
    )


def _sample_times(duration: Decimal, step: Decimal, max_frames: int) -> list[Decimal]:
    times: list[Decimal] = []
    cursor = Decimal("0")
    while cursor < duration:
        times.append(cursor.quantize(Decimal("0.001")))
        cursor += step
    # Stay a few frames before EOF so ffmpeg -ss still returns a picture.
    last = (duration - Decimal("0.05")).quantize(Decimal("0.001"))
    if last > 0 and (not times or last > times[-1]):
        times.append(last)
    if not times:
        times = [Decimal("0")]
    if len(times) <= max_frames:
        return times
    inner = times[1:-1]
    need = max_frames - 2
    if need <= 0:
        return [times[0], times[-1]]
    picked = [inner[int(index * len(inner) / need)] for index in range(need)]
    return [times[0], *picked, times[-1]]


def _fps(ratio: str) -> float:
    try:
        value = float(Fraction(ratio))
    except (ValueError, ZeroDivisionError):
        return 0.0
    return value


def _require_binaries() -> None:
    missing = [name for name in ("ffmpeg", "ffprobe") if shutil.which(name) is None]
    if missing:
        raise EvidencePackError("reconstruct requires local " + " and ".join(missing) + " on PATH")


def _run(args: list[str]) -> str:
    completed = subprocess.run(args, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        err = (completed.stderr or completed.stdout or "unknown ffmpeg error").strip()
        raise EvidencePackError(f"{args[0]} failed: {err[:500]}")
    return completed.stdout
