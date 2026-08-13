from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from omni_rewriter.models.observation import (
    VideoObservation,
    bind_probe_duration,
    camera_uses_h3_type,
    format_timecode,
    parse_timecode,
)


def _observation(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "duration_seconds": "6",
        "invariants": ["A handmade red kite", "Live-action, cinematic"],
        "shots": [
            {
                "index": 1,
                "start": "00:00.000",
                "end": "00:03.000",
                "visual_job": "Lift off the hill",
                "camera": "Static",
                "on_screen_state": "Kite rises; grass stays in frame",
            },
            {
                "index": 2,
                "start": "00:03.000",
                "end": "00:06.000",
                "visual_job": "Bank into sunset",
                "camera": "Arc Shot, small amplitude, slow",
                "on_screen_state": "Hill drops away",
            },
        ],
        "dialogue": [
            {
                "at": "00:04.200",
                "speaker": "S1",
                "language": "English",
                "text": "Hold the line!",
                "inferred": True,
            }
        ],
        "soundscape": "Soft breeze through dry grass.",
        "music": "Two plucked notes, low in the mix.",
        "uncertainties": ["Spoken line is inferred"],
    }
    payload.update(overrides)
    return payload


def test_parse_and_format_timecode() -> None:
    assert parse_timecode("00:04.200") == Decimal("4.200")
    assert format_timecode(Decimal("4.2")) == "00:04.200"
    with pytest.raises(ValueError, match="MM:SS.mmm"):
        parse_timecode("4.2")


def test_camera_types_reject_panic() -> None:
    assert camera_uses_h3_type("Pan left, slow")
    assert camera_uses_h3_type("Arc Shot, small amplitude, slow")
    assert not camera_uses_h3_type("Panic zoom")


def test_video_observation_happy_path() -> None:
    observation = VideoObservation.model_validate(_observation())
    assert observation.shots[0].index == 1
    assert observation.dialogue[0].inferred is True


def test_video_observation_rejects_shot_past_duration() -> None:
    with pytest.raises(ValidationError, match="within duration"):
        VideoObservation.model_validate(_observation(duration_seconds="3"))


def test_video_observation_rejects_dialogue_in_soundscape() -> None:
    with pytest.raises(ValidationError, match="dialogue belongs"):
        VideoObservation.model_validate(_observation(soundscape="Someone says <d>[English] hi</d>"))


def test_bind_probe_duration_revalidates() -> None:
    observation = VideoObservation.model_validate(_observation())
    with pytest.raises(ValidationError):
        bind_probe_duration(observation, Decimal("2"))
    bound = bind_probe_duration(observation, Decimal("6.000"))
    assert bound.duration_seconds == Decimal("6.000")


def test_video_observation_coerces_seconds_to_timecode() -> None:
    payload = _observation()
    shots = payload["shots"]
    assert isinstance(shots, list)
    shots[-1]["end"] = "6.000"
    observation = VideoObservation.model_validate(payload)
    assert observation.shots[-1].end == "00:06.000"
