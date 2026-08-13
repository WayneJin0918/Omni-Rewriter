from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from omni_rewriter.models import (
    BaseRewrite,
    MediaReference,
    MediaRole,
    MediaType,
    Ref2VARewrite,
    RewriteRequest,
    TaskType,
    infer_task,
)
from omni_rewriter.models.validation import (
    labels_in,
    validate_markup,
    validate_reference_numbering,
    validate_timeline,
)
from omni_rewriter.render import H3Renderable, render_h3_prompt


def media(role: MediaRole, uri: str = "frame.png") -> MediaReference:
    kind = (
        MediaType.AUDIO
        if role in {MediaRole.AUDIO_REUSE, MediaRole.AUDIO_REFERENCE}
        else MediaType.IMAGE
    )
    return MediaReference(media_type=kind, role=role, uri=uri)


@pytest.mark.parametrize(
    ("items", "task"),
    [
        ([], TaskType.T2VA),
        ([media(MediaRole.FIRST_FRAME)], TaskType.I2VA),
        ([media(MediaRole.LAST_FRAME)], TaskType.L2VA),
        (
            [media(MediaRole.FIRST_FRAME, "a.png"), media(MediaRole.LAST_FRAME, "b.png")],
            TaskType.FL2VA,
        ),
        ([media(MediaRole.REFERENCE)], TaskType.REF2VA),
    ],
)
def test_infer_task(items: list[MediaReference], task: TaskType) -> None:
    assert infer_task(items) is task


def test_request_rejects_conflicting_task() -> None:
    with pytest.raises(ValidationError, match="conflicts with media"):
        RewriteRequest(
            prompt="move",
            duration_seconds=6,
            task=TaskType.T2VA,
            media=[media(MediaRole.FIRST_FRAME)],
        )


def test_request_rejects_duplicate_uri() -> None:
    with pytest.raises(ValidationError, match="only appear once"):
        RewriteRequest(
            prompt="move",
            duration_seconds=6,
            media=[media(MediaRole.REFERENCE), media(MediaRole.REFERENCE)],
        )


@pytest.mark.parametrize(
    ("kind", "role"),
    [
        (MediaType.VIDEO, MediaRole.FIRST_FRAME),
        (MediaType.IMAGE, MediaRole.AUDIO_REFERENCE),
        (MediaType.AUDIO, MediaRole.SOURCE),
    ],
)
def test_media_rejects_incompatible_roles(kind: MediaType, role: MediaRole) -> None:
    with pytest.raises(ValidationError):
        MediaReference(media_type=kind, role=role, uri="asset.bin")


def test_base_normalizes_colon_shot_headers(base_output: dict[str, object]) -> None:
    base_output["integrated_multimodal_description"] = (
        "[Shot 1]: A kite lifts off the hill. [Shot 2] At 00:03.000: it banks into sunset light."
    )
    output = BaseRewrite.model_validate(base_output)
    body = output.integrated_multimodal_description
    assert "[Shot 1] A kite" in body
    assert "[Shot 2] At 00:03.000, it banks" in body


def test_base_clamps_shot_on_duration(base_output: dict[str, object]) -> None:
    base_output["duration_seconds"] = "6"
    base_output["integrated_multimodal_description"] = (
        "[Shot 1] A kite lifts off the hill. [Shot 2] At 00:06.000, it banks into sunset light."
    )
    output = BaseRewrite.model_validate(base_output)
    assert "[Shot 2] At 00:05.999," in output.integrated_multimodal_description
    output = BaseRewrite.model_validate(base_output)
    rendered = render_h3_prompt(output)
    assert isinstance(output, H3Renderable)
    assert rendered.startswith("integrated_multimodal_description:")
    assert "overall_soundscape:" in rendered


def test_i2va_render_alignment(base_output: dict[str, object]) -> None:
    base_output.update(
        task="i2va",
        integrated_multimodal_description="[Shot 1] <Picture 1> begins to glow.",
    )
    rendered = BaseRewrite.model_validate(base_output).render()
    assert "0.00 seconds" in rendered
    assert "<Picture 1>" in rendered


def test_ref_model_and_render(ref_output: dict[str, object]) -> None:
    output = Ref2VARewrite.model_validate(ref_output)
    assert output.render().count("\n\n") == 5
    assert output.render().startswith("subject_definitions:")


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("[Shot 2] late", "start at 1"),
        ("[Shot 1] start [Shot 2] later", "requires"),
        ("[Shot 1] start [Shot 2] At 00:06.000, end", "before"),
        ("[Shot 1] start [Shot 2] At 00:60.000, end", "less than 60"),
    ],
)
def test_timeline_validation_errors(text: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        validate_timeline(text, Decimal("6"))


@pytest.mark.parametrize(
    "text",
    [
        "<d>[English] </d>",
        "<d>[English] hello",
        "<scenetrans>",
        "(S2) <d>[English] hello</d>",
    ],
)
def test_markup_validation_errors(text: str) -> None:
    with pytest.raises(ValueError):
        validate_markup(text)


def test_reference_helpers() -> None:
    assert labels_in("<Subject 1> sees <Picture 1>") == {"<Subject 1>", "<Picture 1>"}
    with pytest.raises(ValueError, match="contiguous"):
        validate_reference_numbering("<Video 2>")


def test_base_rejects_wrong_picture_labels(base_output: dict[str, object]) -> None:
    base_output["integrated_multimodal_description"] = "[Shot 1] <Picture 1> is visible."
    with pytest.raises(ValidationError, match="requires picture labels"):
        BaseRewrite.model_validate(base_output)


def test_ref_rejects_undefined_label(ref_output: dict[str, object]) -> None:
    ref_output["detailed_description"] += " <Picture 1> appears."
    with pytest.raises(ValidationError, match="undefined"):
        Ref2VARewrite.model_validate(ref_output)
