"""Shared enums and strict model configuration."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    """Base class for stable public request and response schemas."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, validate_assignment=True)


class TaskType(StrEnum):
    T2VA = "t2va"
    I2VA = "i2va"
    FL2VA = "fl2va"
    L2VA = "l2va"
    REF2VA = "ref2va"
    # Image PE (Seedream / Qwen-Image dialects)
    T2I = "t2i"
    I2I = "i2i"
    IMAGE_EDIT = "image_edit"


IMAGE_TASKS = frozenset({TaskType.T2I, TaskType.I2I, TaskType.IMAGE_EDIT})
VIDEO_TASKS = frozenset(
    {TaskType.T2VA, TaskType.I2VA, TaskType.FL2VA, TaskType.L2VA, TaskType.REF2VA}
)


class MediaType(StrEnum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class MediaRole(StrEnum):
    FIRST_FRAME = "first_frame"
    LAST_FRAME = "last_frame"
    REFERENCE = "reference"
    SOURCE = "source"
    AUDIO_REUSE = "audio_reuse"
    AUDIO_REFERENCE = "audio_reference"
