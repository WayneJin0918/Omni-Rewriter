"""Unified rewrite request and deterministic task routing."""

from decimal import Decimal

from pydantic import Field, computed_field, field_validator, model_validator

from .common import IMAGE_TASKS, MediaRole, StrictModel, TaskType
from .media import MediaReference


def infer_task(media: list[MediaReference]) -> TaskType:
    """Infer the narrowest video task from media roles.

    Image tasks (t2i / i2i / image_edit) are never inferred from media alone; they
    must be set explicitly on the request so existing no-media callers stay on t2va.
    """

    if not media:
        return TaskType.T2VA
    roles = [item.role for item in media]
    if len(media) == 1 and roles == [MediaRole.FIRST_FRAME]:
        return TaskType.I2VA
    if len(media) == 1 and roles == [MediaRole.LAST_FRAME]:
        return TaskType.L2VA
    if (
        len(media) == 2
        and roles.count(MediaRole.FIRST_FRAME) == 1
        and roles.count(MediaRole.LAST_FRAME) == 1
    ):
        return TaskType.FL2VA
    return TaskType.REF2VA


class RewriteRequest(StrictModel):
    """Transport-neutral input shared by agents, CLI, and APIs."""

    prompt: str = Field(min_length=1, max_length=100_000)
    duration_seconds: Decimal | None = Field(default=None, gt=0)
    media: list[MediaReference] = Field(default_factory=list, max_length=32)
    task: TaskType | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("prompt")
    @classmethod
    def reject_nul(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("prompt must not contain NUL")
        return value

    @model_validator(mode="after")
    def validate_route(self) -> "RewriteRequest":
        uris = [item.uri for item in self.media]
        if len(uris) != len(set(uris)):
            raise ValueError("the same media uri may only appear once")

        if self.task in IMAGE_TASKS:
            if self.duration_seconds is not None:
                raise ValueError("duration_seconds must be omitted for image tasks")
            if self.task is TaskType.T2I:
                return self
            if not self.media:
                raise ValueError(f"{self.task.value} requires at least one media reference")
            non_image = [item for item in self.media if item.media_type.value != "image"]
            if non_image:
                raise ValueError("image tasks currently accept only image media")
            return self

        if self.duration_seconds is None:
            raise ValueError("duration_seconds is required for video tasks")

        inferred = infer_task(self.media)
        if self.task is TaskType.REF2VA:
            if not self.media:
                raise ValueError("ref2va requires at least one media reference")
        elif self.task is not None and self.task is not inferred:
            raise ValueError(
                f"task {self.task.value!r} conflicts with media; expected {inferred.value!r}"
            )
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def resolved_task(self) -> TaskType:
        if self.task in IMAGE_TASKS:
            return self.task
        return self.task or infer_task(self.media)

    @property
    def image_pe_profile(self) -> str:
        raw = self.metadata.get("image_pe_profile", "").strip().lower()
        if raw:
            return raw
        if self.resolved_task is TaskType.IMAGE_EDIT:
            return "qwen_image_edit"
        return "seedream"
