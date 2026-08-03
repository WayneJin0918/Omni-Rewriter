"""Unified rewrite request and deterministic task routing."""

from decimal import Decimal

from pydantic import Field, computed_field, field_validator, model_validator

from .common import MediaRole, StrictModel, TaskType
from .media import MediaReference


def infer_task(media: list[MediaReference]) -> TaskType:
    """Infer the narrowest H3 task from media roles."""

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
    """Transport-neutral input shared by future agents, CLI, and APIs."""

    prompt: str = Field(min_length=1, max_length=100_000)
    duration_seconds: Decimal = Field(gt=0)
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
        inferred = infer_task(self.media)
        if self.task is TaskType.REF2VA:
            if not self.media:
                raise ValueError("ref2va requires at least one media reference")
        elif self.task is not None and self.task is not inferred:
            raise ValueError(
                f"task {self.task.value!r} conflicts with media; expected {inferred.value!r}"
            )
        uris = [item.uri for item in self.media]
        if len(uris) != len(set(uris)):
            raise ValueError("the same media uri may only appear once")
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def resolved_task(self) -> TaskType:
        return self.task or infer_task(self.media)
