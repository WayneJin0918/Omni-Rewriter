"""Shared application services used by the CLI and HTTP API."""

from __future__ import annotations

from typing import Any, Mapping

from pydantic import ValidationError

from .agent import RewriteAgent, RewriteAgentConfig, RewriteResult
from .backends import OpenAICompatibleBackend
from .config import Settings
from .media_input import MediaInputConfig, MediaPreparer
from .models import BaseRewrite, ImageRewrite, Ref2VARewrite, RewriteOutput, RewriteRequest
from .models.common import IMAGE_TASKS


async def expand(request: RewriteRequest, settings: Settings | None = None) -> RewriteResult:
    settings = settings or Settings.from_env()
    backend = OpenAICompatibleBackend(settings.chat_backend_config())
    media = MediaPreparer(MediaInputConfig(allow_local_files=settings.allow_local_media))
    agent = RewriteAgent(
        backend,
        media_preparer=media,
        config=RewriteAgentConfig(max_repairs=settings.max_repairs),
    )
    try:
        return await agent.run(request)
    finally:
        await backend.aclose()
        await media.aclose()


def validate_output(payload: Mapping[str, Any]) -> tuple[RewriteOutput, RewriteRequest | None]:
    """Validate a direct output object or ``{"request": ..., "output": ...}`` envelope."""

    request_data = payload.get("request")
    output_data = payload.get("output")
    if output_data is None:
        output_data = payload
        request = None
    else:
        if not isinstance(request_data, Mapping):
            raise ValueError("validation envelope requires an object-valued request")
        request = RewriteRequest.model_validate(request_data)
    if not isinstance(output_data, Mapping):
        raise ValueError("output must be a JSON object")

    if request is not None and request.resolved_task in IMAGE_TASKS:
        output: RewriteOutput = ImageRewrite.model_validate(output_data)
    elif "subject_definitions" in output_data or (
        request is not None and request.resolved_task.value == "ref2va"
    ):
        output = Ref2VARewrite.model_validate(output_data)
    elif "ratio" in output_data and "integrated_multimodal_description" not in output_data:
        output = ImageRewrite.model_validate(output_data)
    else:
        output = BaseRewrite.model_validate(output_data)

    if request is not None:
        if isinstance(output, ImageRewrite):
            if output.task is not request.resolved_task:
                raise ValueError("output task does not match request")
        else:
            if output.duration_seconds != request.duration_seconds:
                raise ValueError("output duration_seconds does not match request")
            if isinstance(output, BaseRewrite) and output.task is not request.resolved_task:
                raise ValueError("output task does not match request")
    return output, request


def validation_error(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, ValidationError):
        return {"valid": False, "errors": exc.errors(include_url=False)}
    return {"valid": False, "errors": [{"type": type(exc).__name__, "msg": str(exc)}]}
