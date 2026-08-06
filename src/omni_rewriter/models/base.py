"""Three-section H3 output for T2VA and keyframe tasks."""

import re
from decimal import ROUND_HALF_UP, Decimal

from pydantic import Field, model_validator

from .common import StrictModel, TaskType
from .validation import labels_in, validate_markup, validate_reference_numbering, validate_timeline


def _duration(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


class BaseRewrite(StrictModel):
    """Validated three-section H3 rewrite."""

    task: TaskType
    duration_seconds: Decimal = Field(gt=0)
    integrated_multimodal_description: str = Field(min_length=1)
    overall_soundscape: str = Field(min_length=1)
    non_diegetic_music: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_h3_grammar(self) -> "BaseRewrite":
        if self.task is TaskType.REF2VA:
            raise ValueError("ref2va requires Ref2VARewrite")
        body = self.integrated_multimodal_description
        validate_timeline(body, self.duration_seconds)
        validate_markup(body)
        validate_reference_numbering(body)
        pictures = {label for label in labels_in(body) if label.startswith("<Picture ")}
        expected = {
            TaskType.T2VA: set(),
            TaskType.I2VA: {"<Picture 1>"},
            TaskType.FL2VA: {"<Picture 1>", "<Picture 2>"},
            TaskType.L2VA: {"<Picture 1>"},
        }[self.task]
        if pictures != expected:
            raise ValueError(
                f"{self.task.value} description requires picture labels {sorted(expected)}"
            )
        if "<d>" in self.overall_soundscape or "<d>" in self.non_diegetic_music:
            raise ValueError("dialogue belongs only in integrated_multimodal_description")
        return self

    def render(self) -> str:
        """Render the exact prompt text sent to H3."""

        body = self.integrated_multimodal_description
        shots = len(re.findall(r"\[Shot [1-9]\d*\]", body))
        duration = _duration(self.duration_seconds)
        instruction: str | None = None
        if self.task is TaskType.I2VA:
            instruction = (
                "For the target video, at 0.00 seconds into the target video, "
                "<Picture 1> (from [Shot 1]) is fully referenced."
            )
        elif self.task is TaskType.FL2VA:
            instruction = (
                "How the reference pictures align with the target video — "
                "Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; "
                f"Picture 2 (from Shot {shots}) aligns with the {duration}-second mark "
                "of the target video."
            )
        elif self.task is TaskType.L2VA:
            instruction = (
                "How the reference pictures align with the target video — "
                f"<Picture 1> (from [Shot {shots}]) aligns with the {duration}-second mark "
                "of the target video."
            )
        sections = (
            f"integrated_multimodal_description: {body}\n\n"
            f"overall_soundscape: {self.overall_soundscape}\n\n"
            f"non_diegetic_music: {self.non_diegetic_music}"
        )
        return f"{instruction}\n\n{sections}" if instruction else sections
