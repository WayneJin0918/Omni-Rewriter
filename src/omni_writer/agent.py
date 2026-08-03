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
from .models import BaseRewrite, Ref2VARewrite, RewriteOutput, RewriteRequest, TaskType
from .models.common import StrictModel
from .prompts import (
    ANALYZE_SYSTEM_PROMPT,
    draft_system_prompt,
    repair_system_prompt,
    request_context,
)
from .trace import JSONLTrace

_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL | re.IGNORECASE)


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
        response_model: type[BaseRewrite] | type[Ref2VARewrite]
        response_model = Ref2VARewrite if task is TaskType.REF2VA else BaseRewrite
        await self._event(
            run_id,
            AgentState.ANALYZE,
            task=task.value,
            prompt_characters=len(request.prompt),
            media_count=len(request.media),
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
                {"role": "system", "content": draft_system_prompt(task, response_model)},
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
                candidate_raw = await self.backend.complete(
                    [
                        {
                            "role": "system",
                            "content": repair_system_prompt(response_model),
                        },
                        {
                            "role": "user",
                            "content": json.dumps(
                                {
                                    "invalid_candidate": candidate_raw,
                                    "validation_errors": last_error,
                                    "required_task": task.value,
                                    "required_duration_seconds": str(
                                        request.duration_seconds
                                    ),
                                },
                                ensure_ascii=False,
                            ),
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
        response_model: type[BaseRewrite] | type[Ref2VARewrite],
    ) -> RewriteOutput:
        output = response_model.model_validate(self._parse_json(raw))
        if output.duration_seconds != request.duration_seconds:
            raise ValueError(
                "duration_seconds must exactly match the request "
                f"({request.duration_seconds})"
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
