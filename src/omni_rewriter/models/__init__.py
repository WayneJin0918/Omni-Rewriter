"""Public Pydantic models for Omni-Rewriter."""

from .base import BaseRewrite
from .common import IMAGE_TASKS, VIDEO_TASKS, MediaRole, MediaType, TaskType
from .image import ALLOWED_RATIOS, ImagePEProfile, ImageRewrite
from .lingbot import (
    LingBotAction,
    LingBotCameraInfo,
    LingBotCaption,
    LingBotCaptionContent,
    LingBotProminentElement,
    LingBotVideoDescription,
)
from .media import MediaReference
from .ref2va import Ref2VARewrite
from .request import RewriteRequest, infer_task

RewriteOutput = BaseRewrite | Ref2VARewrite | ImageRewrite

__all__ = [
    "ALLOWED_RATIOS",
    "BaseRewrite",
    "IMAGE_TASKS",
    "ImagePEProfile",
    "ImageRewrite",
    "LingBotAction",
    "LingBotCameraInfo",
    "LingBotCaption",
    "LingBotCaptionContent",
    "LingBotProminentElement",
    "LingBotVideoDescription",
    "MediaReference",
    "MediaRole",
    "MediaType",
    "Ref2VARewrite",
    "RewriteOutput",
    "RewriteRequest",
    "TaskType",
    "VIDEO_TASKS",
    "infer_task",
]
