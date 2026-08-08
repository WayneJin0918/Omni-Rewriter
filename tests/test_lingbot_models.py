from __future__ import annotations

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from omni_rewriter.models import LingBotCaption

_cases_env = os.environ.get("LINGBOT_VIDEO_CASES", "").strip()
UPSTREAM_CASES = Path(_cases_env) if _cases_env else None


def image_caption() -> dict[str, object]:
    return {
        "caption": {
            "comprehensive_description": "A red cup rests on a wooden table.",
            "camera_info": {
                "color": "Warm",
                "frame_size": "Close Up",
                "shot_type_angle": "Eye level",
                "lens_size": "Medium",
                "composition": "Center",
                "lighting": "Soft light",
                "lighting_type": "Daylight",
            },
            "world_knowledge": [],
            "prominent_elements": [
                {
                    "name": "red cup",
                    "description": "A small ceramic cup.",
                    "location": "center",
                    "relative_size": "medium",
                    "shape_and_color": "cylindrical and red",
                    "texture": "glossy ceramic",
                    "appearance_details": "",
                    "relationship": "resting on the table",
                    "orientation": "upright",
                }
            ],
        }
    }


def video_caption() -> dict[str, object]:
    value = image_caption()
    caption = value["caption"]
    assert isinstance(caption, dict)
    caption["comprehensive_description"] = {
        "scene_content_description": "A red cup slides across a wooden table.",
        "camera_movement_description": "The camera remains stationary.",
    }
    elements = caption["prominent_elements"]
    assert isinstance(elements, list)
    assert isinstance(elements[0], dict)
    elements[0]["actions"] = [
        {"timestamp": "[0.0s - 5.0s]", "action": "slowly slides to the right"}
    ]
    value["duration"] = 5
    return value


@pytest.mark.skipif(
    UPSTREAM_CASES is None or not UPSTREAM_CASES.is_dir(),
    reason="LINGBOT_VIDEO_CASES unset or not a directory",
)
def test_all_upstream_caption_examples_validate() -> None:
    assert UPSTREAM_CASES is not None
    paths = sorted(UPSTREAM_CASES.glob("**/prompt.json"))
    assert len(paths) == 15
    for path in paths:
        LingBotCaption.model_validate_json(path.read_text(encoding="utf-8"))


def test_caption_distinguishes_still_image_and_video() -> None:
    assert LingBotCaption.model_validate(image_caption()).duration is None
    assert LingBotCaption.model_validate(video_caption()).duration == 5

    invalid_video = video_caption()
    invalid_video.pop("duration")
    with pytest.raises(ValidationError, match="video captions require duration"):
        LingBotCaption.model_validate(invalid_video)

    invalid_image = image_caption()
    invalid_image["duration"] = 5
    with pytest.raises(ValidationError, match="image captions must omit duration"):
        LingBotCaption.model_validate(invalid_image)


def test_cluster_count_is_consistent() -> None:
    value = image_caption()
    caption = value["caption"]
    assert isinstance(caption, dict)
    elements = caption["prominent_elements"]
    assert isinstance(elements, list)
    assert isinstance(elements[0], dict)
    elements[0]["is_cluster"] = True
    with pytest.raises(ValidationError, match="number_of_objects"):
        LingBotCaption.model_validate(value)
