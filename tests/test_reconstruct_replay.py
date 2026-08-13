from decimal import Decimal

from omni_rewriter.models import BaseRewrite, RewriteRequest, TaskType
from omni_rewriter.reconstruct.replay import (
    clamp_h3_pe_for_generate,
    envelope_for_h3_replay,
    h3_replay_window_seconds,
)


def _long_output() -> BaseRewrite:
    return BaseRewrite.model_validate(
        {
            "task": "t2va",
            "duration_seconds": "20",
            "integrated_multimodal_description": (
                "[Shot 1] A clay fox turns toward camera on a workbench. "
                "[Shot 2] At 00:08.000, the camera Push In toward its eyes. "
                "[Shot 3] At 00:16.500, a Tracking Shot follows it off the table."
            ),
            "overall_soundscape": "Soft clay scrapes and room tone.",
            "non_diegetic_music": "A light pizzicato motif.",
        }
    )


def test_h3_replay_window_floors_and_caps() -> None:
    assert h3_replay_window_seconds(Decimal("10.125")) == 10
    assert h3_replay_window_seconds(Decimal("15.083")) == 15
    assert h3_replay_window_seconds(Decimal("20")) == 15
    assert h3_replay_window_seconds(Decimal("40")) == 15


def test_clamp_drops_shots_at_or_after_window() -> None:
    clamped = clamp_h3_pe_for_generate(_long_output(), 15)
    assert clamped.duration_seconds == Decimal("15")
    assert "[Shot 2]" in clamped.integrated_multimodal_description
    assert "[Shot 3]" not in clamped.integrated_multimodal_description


def test_envelope_for_h3_replay_matches_request_and_output() -> None:
    request = RewriteRequest(
        prompt="reconstruct fixture",
        duration_seconds=Decimal("20"),
        task=TaskType.T2VA,
        metadata={"video_pe_profile": "h3", "reconstruct": "v1-t2va"},
    )
    payload = {
        "request": request.model_dump(mode="json"),
        "output": _long_output().model_dump(mode="json"),
    }
    envelope = envelope_for_h3_replay(payload)
    assert envelope["h3_replay_window_seconds"] == 15
    assert envelope["request"]["duration_seconds"] == "15"
    assert envelope["output"]["duration_seconds"] == "15"
    assert envelope["request"]["metadata"]["h3_replay_window_seconds"] == "15"
    BaseRewrite.model_validate(envelope["output"])
