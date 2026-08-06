"""Media references accepted by every Omni-Rewriter entry point."""

from pydantic import Field, field_validator, model_validator

from .common import MediaRole, MediaType, StrictModel


class MediaReference(StrictModel):
    """A caller-owned asset and its semantic role in the target video."""

    media_type: MediaType
    role: MediaRole = MediaRole.REFERENCE
    uri: str = Field(min_length=1, max_length=4096)
    name: str | None = Field(default=None, max_length=256)
    mime_type: str | None = Field(default=None, max_length=128)

    @field_validator("uri")
    @classmethod
    def reject_control_characters(cls, value: str) -> str:
        if any(ord(char) < 32 for char in value):
            raise ValueError("uri must not contain control characters")
        return value

    @model_validator(mode="after")
    def validate_role_for_type(self) -> "MediaReference":
        image_only = {MediaRole.FIRST_FRAME, MediaRole.LAST_FRAME}
        audio_only = {MediaRole.AUDIO_REUSE, MediaRole.AUDIO_REFERENCE}
        if self.role in image_only and self.media_type is not MediaType.IMAGE:
            raise ValueError(f"{self.role.value} requires image media")
        if self.role in audio_only and self.media_type is not MediaType.AUDIO:
            raise ValueError(f"{self.role.value} requires audio media")
        if self.role is MediaRole.SOURCE and self.media_type is MediaType.AUDIO:
            raise ValueError("source role requires image or video media")
        return self
