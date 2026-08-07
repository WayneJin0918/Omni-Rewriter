"""Typed structured-caption models consumed by LingBot-Video."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, model_validator

from .common import StrictModel

NonEmptyText = Annotated[str, Field(min_length=1)]


class LingBotAction(StrictModel):
    timestamp: NonEmptyText
    action: str


class LingBotCameraInfo(StrictModel):
    color: NonEmptyText
    frame_size: NonEmptyText
    shot_type_angle: NonEmptyText
    lens_size: NonEmptyText
    composition: NonEmptyText
    lighting: NonEmptyText
    lighting_type: NonEmptyText


class LingBotVideoDescription(StrictModel):
    scene_content_description: NonEmptyText
    camera_movement_description: str


class LingBotProminentElement(StrictModel):
    name: NonEmptyText
    description: NonEmptyText
    actions: list[LingBotAction] | None = None
    location: NonEmptyText
    relative_size: NonEmptyText
    shape_and_color: NonEmptyText
    texture: NonEmptyText
    appearance_details: str
    relationship: str
    orientation: NonEmptyText
    pose: str | None = None
    expression: str | None = None
    clothing: str | None = None
    gender: str | None = None
    skin_tone_and_texture: str | None = None
    is_cluster: bool | None = None
    number_of_objects: str | None = None

    @model_validator(mode="after")
    def validate_cluster(self) -> "LingBotProminentElement":
        if self.is_cluster is True and not self.number_of_objects:
            raise ValueError("cluster elements require number_of_objects")
        if self.number_of_objects and self.is_cluster is not True:
            raise ValueError("number_of_objects requires is_cluster=true")
        return self


class LingBotCaptionContent(StrictModel):
    comprehensive_description: NonEmptyText | LingBotVideoDescription
    camera_info: LingBotCameraInfo
    world_knowledge: list[str]
    prominent_elements: Annotated[list[LingBotProminentElement], Field(min_length=1)]


class LingBotCaption(StrictModel):
    """A complete ``prompt.json`` accepted by upstream LingBot inference."""

    caption: LingBotCaptionContent
    duration: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_media_kind(self) -> "LingBotCaption":
        is_video = isinstance(
            self.caption.comprehensive_description,
            LingBotVideoDescription,
        )
        if is_video and self.duration is None:
            raise ValueError("video captions require duration")
        if not is_video and self.duration is not None:
            raise ValueError("image captions must omit duration")
        return self
