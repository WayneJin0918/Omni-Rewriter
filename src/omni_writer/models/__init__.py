"""Public Pydantic models for Omni-Writer."""

from .base import BaseRewrite
from .common import MediaRole, MediaType, TaskType
from .media import MediaReference
from .ref2va import Ref2VARewrite
from .request import RewriteRequest, infer_task

RewriteOutput = BaseRewrite | Ref2VARewrite

__all__ = [
    "BaseRewrite",
    "MediaReference",
    "MediaRole",
    "MediaType",
    "Ref2VARewrite",
    "RewriteOutput",
    "RewriteRequest",
    "TaskType",
    "infer_task",
]
