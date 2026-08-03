from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture
def base_output() -> dict[str, Any]:
    return {
        "task": "t2va",
        "duration_seconds": "6",
        "integrated_multimodal_description": (
            "[Shot 1] A paper kite rises above a quiet hill. "
            "[Shot 2] At 00:03.000, it turns toward warm sunset light."
        ),
        "overall_soundscape": "Soft wind and distant grass movement.",
        "non_diegetic_music": "A restrained two-note string motif.",
    }


@pytest.fixture
def analysis_output() -> dict[str, Any]:
    return {
        "intent": "Show one clear upward movement.",
        "observable_media_facts": [],
        "timing_and_motion": ["The turn happens halfway through."],
        "audio_and_dialogue": ["No dialogue."],
        "continuity_risks": [],
        "constraints": ["Keep the kite visible."],
    }


@pytest.fixture
def ref_output() -> dict[str, Any]:
    return {
        "duration_seconds": "6",
        "subject_definitions": "<Subject 1> A small red paper kite with a white tail.",
        "summary": "[reference generation] A kite crosses a calm evening sky.",
        "retention_analysis": (
            "<Subject 1>: fully_preserved - Keep its red paper body and white tail."
        ),
        "detailed_description": (
            "[Shot 1] <Subject 1> climbs through a pale sky. "
            "[Shot 2] At 00:03.000, <Subject 1> banks gently left."
        ),
        "overall_soundscape": "Light wind passes over the hill.",
        "non_diegetic_music": "Sparse plucked strings.",
    }


@pytest.fixture
def png_bytes() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * 24
