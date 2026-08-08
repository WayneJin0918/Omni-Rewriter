"""Bounded analyze/draft/validate/repair state machine."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import Field, ValidationError

from .backends import ChatBackend
from .errors import RepairExhaustedError, StructuredOutputError
from .media_input import MediaPreparer
from .models import (
    BaseRewrite,
    ImageRewrite,
    Ref2VARewrite,
    RewriteOutput,
    RewriteRequest,
    SeedanceRewrite,
    TaskType,
)
from .models.common import IMAGE_TASKS, StrictModel
from .models.image import IMAGE_REF_RE, ImagePEProfile
from .models.seedance import VideoPEProfile, validate_seedance_against_request
from .prompts import (
    ANALYZE_SYSTEM_PROMPT,
    draft_system_prompt,
    repair_system_prompt,
    request_context,
)
from .trace import JSONLTrace

_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL | re.IGNORECASE)

ResponseModel = type[BaseRewrite] | type[Ref2VARewrite] | type[ImageRewrite] | type[SeedanceRewrite]
Profile = ImagePEProfile | VideoPEProfile | None


class AgentState(StrEnum):
    ANALYZE = "analyze"
    DRAFT = "draft"
    VALIDATE = "validate"
    REPAIR = "repair"
    COMPLETE = "complete"
    FAILED = "failed"


class AnalysisPlan(StrictModel):
    """Structured handoff from multimodal analysis to drafting."""

    intent: str = Field(min_length=1)
    observable_media_facts: list[str] = Field(default_factory=list)
    timing_and_motion: list[str] = Field(default_factory=list)
    audio_and_dialogue: list[str] = Field(default_factory=list)
    continuity_risks: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class RewriteAgentConfig(StrictModel):
    """Bounds and optional trace destination for one agent."""

    max_repairs: int = Field(default=2, ge=0, le=10)
    trace_path: Path | None = None


@dataclass(frozen=True, slots=True)
class RewriteResult:
    output: RewriteOutput
    analysis: AnalysisPlan
    repairs: int
    run_id: str


class RewriteAgent:
    """Orchestrate an LLM backend around deterministic Pydantic validation."""

    def __init__(
        self,
        backend: ChatBackend,
        *,
        media_preparer: MediaPreparer | None = None,
        config: RewriteAgentConfig | None = None,
    ) -> None:
        self.backend = backend
        self.media_preparer = media_preparer or MediaPreparer()
        self.config = config or RewriteAgentConfig()
        self.trace = JSONLTrace(self.config.trace_path) if self.config.trace_path else None

    async def run(self, request: RewriteRequest) -> RewriteResult:
        """Execute the state machine and return a validated rewrite."""

        run_id = uuid4().hex
        task = request.resolved_task
        image_profile = _resolve_image_profile(request) if task in IMAGE_TASKS else None
        video_profile = (
            _resolve_video_profile(request) if task not in IMAGE_TASKS else VideoPEProfile.H3
        )
        profile: Profile = image_profile if image_profile is not None else video_profile
        response_model: ResponseModel
        if task in IMAGE_TASKS:
            response_model = ImageRewrite
        elif video_profile is VideoPEProfile.SEEDANCE:
            if task not in {TaskType.T2VA, TaskType.REF2VA}:
                raise ValueError("Seedance video PE currently supports only t2va and ref2va tasks")
            response_model = SeedanceRewrite
        elif task is TaskType.REF2VA:
            response_model = Ref2VARewrite
        else:
            response_model = BaseRewrite
        await self._event(
            run_id,
            AgentState.ANALYZE,
            task=task.value,
            prompt_characters=len(request.prompt),
            media_count=len(request.media),
            image_pe_profile=image_profile.value if image_profile else None,
            video_pe_profile=video_profile.value if task not in IMAGE_TASKS else None,
        )

        analysis_message = await self.media_preparer.prepare_message(
            request_context(request),
            request.media,
        )
        analysis_raw = await self.backend.complete(
            [
                {"role": "system", "content": ANALYZE_SYSTEM_PROMPT},
                analysis_message,
            ],
            response_model=AnalysisPlan,
        )
        try:
            analysis = AnalysisPlan.model_validate(self._parse_json(analysis_raw))
        except (ValidationError, StructuredOutputError) as exc:
            await self._event(run_id, AgentState.FAILED, error=self._error_text(exc))
            raise StructuredOutputError("analysis response is not a valid AnalysisPlan") from exc

        await self._event(run_id, AgentState.DRAFT, analysis=analysis.model_dump())
        draft_raw = await self.backend.complete(
            [
                {
                    "role": "system",
                    "content": draft_system_prompt(task, response_model, profile=profile),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "request": json.loads(request_context(request)),
                            "analysis": analysis.model_dump(mode="json"),
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            response_model=response_model,
        )

        candidate_raw = draft_raw
        last_error = "unknown validation failure"
        for repairs in range(self.config.max_repairs + 1):
            await self._event(run_id, AgentState.VALIDATE, attempt=repairs + 1)
            try:
                output = self._validate(candidate_raw, request, response_model)
            except (ValidationError, StructuredOutputError, ValueError) as exc:
                last_error = self._error_text(exc)
                await self._event(
                    run_id,
                    AgentState.VALIDATE,
                    attempt=repairs + 1,
                    valid=False,
                    error=last_error,
                    candidate=candidate_raw,
                )
                if repairs >= self.config.max_repairs:
                    break
                await self._event(run_id, AgentState.REPAIR, repair=repairs + 1)
                repair_payload: dict[str, Any] = {
                    "invalid_candidate": candidate_raw,
                    "validation_errors": last_error,
                    "required_task": task.value,
                }
                if request.duration_seconds is not None:
                    repair_payload["required_duration_seconds"] = str(request.duration_seconds)
                if image_profile is not None:
                    repair_payload["required_profile"] = image_profile.value
                if task not in IMAGE_TASKS:
                    repair_payload["required_video_pe_profile"] = video_profile.value
                candidate_raw = await self.backend.complete(
                    [
                        {
                            "role": "system",
                            "content": repair_system_prompt(
                                response_model,
                                image=task in IMAGE_TASKS,
                                profile=profile,
                            ),
                        },
                        {
                            "role": "user",
                            "content": json.dumps(repair_payload, ensure_ascii=False),
                        },
                    ],
                    response_model=response_model,
                )
                continue

            await self._event(
                run_id,
                AgentState.COMPLETE,
                repairs=repairs,
                output=output.model_dump(mode="json"),
            )
            return RewriteResult(
                output=output,
                analysis=analysis,
                repairs=repairs,
                run_id=run_id,
            )

        await self._event(
            run_id,
            AgentState.FAILED,
            error=last_error,
            repairs=self.config.max_repairs,
        )
        raise RepairExhaustedError(
            f"rewrite remained invalid after {self.config.max_repairs} repairs: {last_error}"
        )

    @staticmethod
    def _parse_json(raw: str) -> Any:
        match = _FENCE_RE.match(raw)
        if match:
            raw = match.group(1)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise StructuredOutputError(
                f"response is not JSON at line {exc.lineno}, column {exc.colno}"
            ) from exc

    def _validate(
        self,
        raw: str,
        request: RewriteRequest,
        response_model: ResponseModel,
    ) -> RewriteOutput:
        output = response_model.model_validate(self._parse_json(raw))
        if isinstance(output, ImageRewrite):
            if output.task is not request.resolved_task:
                raise ValueError(
                    f"task must exactly match the request ({request.resolved_task.value})"
                )
            expected_profile = _resolve_image_profile(request)
            if output.profile is not expected_profile:
                raise ValueError(
                    f"profile must exactly match the request ({expected_profile.value})"
                )
            if output.ratio.startswith("[image"):
                match = IMAGE_REF_RE.fullmatch(output.ratio)
                if match is None:
                    raise ValueError("ratio [image N] is malformed")
                index = int(match.group(1))
                if index < 1 or index > len(request.media):
                    raise ValueError(
                        f"ratio {output.ratio} references a missing image "
                        f"(media count={len(request.media)})"
                    )
            return output
        if isinstance(output, SeedanceRewrite):
            validate_seedance_against_request(
                output,
                media_count=len(request.media),
                task=request.resolved_task,
                duration_seconds=request.duration_seconds,
            )
            return output
        if output.duration_seconds != request.duration_seconds:
            raise ValueError(
                f"duration_seconds must exactly match the request ({request.duration_seconds})"
            )
        if isinstance(output, BaseRewrite) and output.task is not request.resolved_task:
            raise ValueError(f"task must exactly match the request ({request.resolved_task.value})")
        return output

    async def _event(self, run_id: str, state: AgentState, **payload: Any) -> None:
        if self.trace is not None:
            await self.trace.write("agent_state", run_id=run_id, state=state.value, **payload)

    @staticmethod
    def _error_text(exc: Exception) -> str:
        if isinstance(exc, ValidationError):
            return exc.json(include_url=False)
        return str(exc)


def _resolve_image_profile(request: RewriteRequest) -> ImagePEProfile:
    raw = request.image_pe_profile
    try:
        return ImagePEProfile(raw)
    except ValueError as exc:
        raise ValueError(
            "metadata.image_pe_profile must be 'seedream' or 'qwen_image_edit'"
        ) from exc


def _resolve_video_profile(request: RewriteRequest) -> VideoPEProfile:
    raw = request.video_pe_profile
    try:
        return VideoPEProfile(raw)
    except ValueError as exc:
        raise ValueError("metadata.video_pe_profile must be 'h3' or 'seedance'") from exc
