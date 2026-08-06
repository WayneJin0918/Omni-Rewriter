"""Unit tests for Seedream / Qwen-Image-Edit image PE models and routing."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from omni_rewriter.models import (
    ImagePEProfile,
    ImageRewrite,
    MediaReference,
    MediaRole,
    MediaType,
    RewriteRequest,
    TaskType,
)
from omni_rewriter.service import validate_output


def test_t2i_request_omits_duration() -> None:
    req = RewriteRequest(prompt="a red bicycle on wet asphalt at night", task=TaskType.T2I)
    assert req.resolved_task is TaskType.T2I
    assert req.image_pe_profile == "seedream"


def test_t2i_rejects_duration() -> None:
    with pytest.raises(ValidationError, match="duration_seconds must be omitted"):
        RewriteRequest(
            prompt="a red bicycle",
            duration_seconds=6,
            task=TaskType.T2I,
        )


def test_video_still_requires_duration() -> None:
    with pytest.raises(ValidationError, match="duration_seconds is required"):
        RewriteRequest(prompt="a kite above a hill")


def test_i2i_requires_media() -> None:
    with pytest.raises(ValidationError, match="requires at least one media"):
        RewriteRequest(prompt="keep the face, change jacket to leather", task=TaskType.I2I)


def test_image_edit_defaults_qwen_profile() -> None:
    req = RewriteRequest(
        prompt="把裙子换成红色丝绒",
        task=TaskType.IMAGE_EDIT,
        media=[
            MediaReference(
                media_type=MediaType.IMAGE,
                role=MediaRole.REFERENCE,
                uri="ref.png",
            )
        ],
    )
    assert req.image_pe_profile == "qwen_image_edit"


def test_image_rewrite_seedream_render() -> None:
    out = ImageRewrite(
        task=TaskType.T2I,
        profile=ImagePEProfile.SEEDREAM,
        prompt='A square product photo of a ceramic mug printed with "Hello".',
        ratio="1:1",
    )
    rendered = out.render()
    assert "<prompt>" in rendered and "<ratio>" in rendered
    assert "1:1" in rendered


def test_image_rewrite_qwen_render_is_prompt_only() -> None:
    out = ImageRewrite(
        task=TaskType.IMAGE_EDIT,
        profile=ImagePEProfile.QWEN_IMAGE_EDIT,
        prompt="Keep the woman from image 1, replace the background with a rainy Tokyo street.",
        ratio="[image 1]",
    )
    assert out.render() == out.prompt


def test_image_rewrite_rejects_bad_ratio() -> None:
    with pytest.raises(ValidationError, match="ratio must be one of"):
        ImageRewrite(
            task=TaskType.T2I,
            prompt="A wide coastal cliff at sunrise with layered clouds.",
            ratio="5:4",
        )


def test_image_rewrite_rejects_multiline_prompt() -> None:
    with pytest.raises(ValidationError, match="single paragraph"):
        ImageRewrite(
            task=TaskType.T2I,
            prompt="line one\nline two",
            ratio="16:9",
        )


def test_validate_output_image_envelope() -> None:
    payload = {
        "request": {"prompt": "neon ramen shop sign reading “営業中”", "task": "t2i"},
        "output": {
            "task": "t2i",
            "profile": "seedream",
            "prompt": 'A night street storefront with a neon sign reading “営業中”.',
            "ratio": "3:2",
        },
    }
    output, request = validate_output(payload)
    assert isinstance(output, ImageRewrite)
    assert request is not None
    assert request.resolved_task is TaskType.T2I
