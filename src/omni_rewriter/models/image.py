"""Image PE outputs for Seedream and Qwen-Image-Edit dialects."""

from __future__ import annotations

import re
from enum import StrEnum

from pydantic import Field, field_validator

from .common import StrictModel, TaskType

ALLOWED_RATIOS = frozenset({"21:9", "16:9", "3:2", "4:3", "1:1", "3:4", "2:3", "9:16"})
RATIO_RE = re.compile(r"^(?:\d+:\d+|\[image [1-9]\d*\])$")
IMAGE_REF_RE = re.compile(r"\[image ([1-9]\d*)\]")


class ImagePEProfile(StrEnum):
    """Dialect controlling drafting rules and render packaging."""

    SEEDREAM = "seedream"
    QWEN_IMAGE_EDIT = "qwen_image_edit"


class ImageRewrite(StrictModel):
    """Validated image prompt expansion: one paragraph + aspect ratio."""

    task: TaskType
    profile: ImagePEProfile = ImagePEProfile.SEEDREAM
    prompt: str = Field(min_length=1, max_length=20_000)
    ratio: str = Field(min_length=1, max_length=32)

    @field_validator("task")
    @classmethod
    def require_image_task(cls, value: TaskType) -> TaskType:
        if value not in {TaskType.T2I, TaskType.I2I, TaskType.IMAGE_EDIT}:
            raise ValueError("ImageRewrite.task must be t2i, i2i, or image_edit")
        return value

    @field_validator("prompt")
    @classmethod
    def single_paragraph(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("prompt must not be empty")
        if "\n" in stripped or "\r" in stripped:
            raise ValueError("prompt must be a single paragraph without newlines")
        return stripped

    @field_validator("ratio")
    @classmethod
    def validate_ratio(cls, value: str) -> str:
        stripped = value.strip()
        if not RATIO_RE.fullmatch(stripped):
            raise ValueError("ratio must be one of 21:9,16:9,3:2,4:3,1:1,3:4,2:3,9:16 or [image N]")
        if ":" in stripped and stripped not in ALLOWED_RATIOS:
            raise ValueError("ratio must be one of 21:9,16:9,3:2,4:3,1:1,3:4,2:3,9:16 or [image N]")
        return stripped

    def render(self) -> str:
        """Seedream-compatible tagged block; Qwen edit defaults to prompt body."""

        if self.profile is ImagePEProfile.QWEN_IMAGE_EDIT:
            return self.prompt
        return f"<prompt>\n{self.prompt}\n</prompt>\n<ratio>\n{self.ratio}\n</ratio>"

    def render_seedream(self) -> str:
        return f"<prompt>\n{self.prompt}\n</prompt>\n<ratio>\n{self.ratio}\n</ratio>"
