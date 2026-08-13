"""Clamp reconstruct PE onto the public H3 generate window (integer 4–15s).

Observe / expand may keep the full ffprobe duration. Generate is a separate adapter
step and must not send 20s/40s ``duration_seconds`` to public MiniMax-H3.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from ..errors import ReconstructError
from ..models import BaseRewrite, RewriteRequest
from ..models.validation import SHOT_RE, validate_timeline

H3_GENERATE_MIN_SECONDS = 4
H3_GENERATE_MAX_SECONDS = 15


def h3_replay_window_seconds(duration: Decimal) -> int:
    """Integer H3 generate length: min(15, floor(source duration)), at least 4."""

    window = min(H3_GENERATE_MAX_SECONDS, int(duration))
    if window < H3_GENERATE_MIN_SECONDS:
        raise ReconstructError(
            f"H3 generate window is {H3_GENERATE_MIN_SECONDS}-{H3_GENERATE_MAX_SECONDS}s; "
            f"clip is {duration}s"
        )
    return window


def clamp_h3_pe_for_generate(output: BaseRewrite, window_seconds: int) -> BaseRewrite:
    """Drop shots at or after ``window_seconds`` and lock duration to that integer."""

    if not H3_GENERATE_MIN_SECONDS <= window_seconds <= H3_GENERATE_MAX_SECONDS:
        raise ReconstructError(
            "H3 generate window must be an integer from "
            f"{H3_GENERATE_MIN_SECONDS} through {H3_GENERATE_MAX_SECONDS} seconds"
        )
    duration = Decimal(window_seconds)
    body = output.integrated_multimodal_description
    matches = list(SHOT_RE.finditer(body))
    if not matches:
        raise ReconstructError("H3 PE is missing [Shot 1]")
    cut_at = len(body)
    for match in matches[1:]:
        stamp = match["time"]
        if stamp is None:
            continue
        minutes, seconds = stamp.split(":")
        current = Decimal(minutes) * 60 + Decimal(seconds)
        if current >= duration:
            cut_at = match.start()
            break
    new_body = body[:cut_at].rstrip()
    validate_timeline(new_body, duration)
    return BaseRewrite.model_validate(
        {
            **output.model_dump(mode="json"),
            "duration_seconds": str(duration),
            "integrated_multimodal_description": new_body,
        }
    )


def clamp_request_for_h3(request: RewriteRequest, window_seconds: int) -> RewriteRequest:
    """Copy a reconstruct request onto the integer H3 generate window."""

    if not H3_GENERATE_MIN_SECONDS <= window_seconds <= H3_GENERATE_MAX_SECONDS:
        raise ReconstructError(
            "H3 generate window must be an integer from "
            f"{H3_GENERATE_MIN_SECONDS} through {H3_GENERATE_MAX_SECONDS} seconds"
        )
    metadata = dict(request.metadata)
    metadata["h3_replay_window_seconds"] = str(window_seconds)
    return request.model_copy(
        update={
            "duration_seconds": Decimal(window_seconds),
            "metadata": metadata,
        }
    )


def envelope_for_h3_replay(payload: dict[str, Any]) -> dict[str, Any]:
    """Build a generate envelope from a reconstruct JSON payload."""

    raw_request = dict(payload["request"])
    raw_request.pop("resolved_task", None)
    request = RewriteRequest.model_validate(raw_request)
    output = BaseRewrite.model_validate(payload["output"])
    duration = request.duration_seconds
    if duration is None:
        duration = output.duration_seconds
    window = h3_replay_window_seconds(duration)
    clamped_request = clamp_request_for_h3(request, window)
    clamped_output = clamp_h3_pe_for_generate(output, window)
    return {
        "request": clamped_request.model_dump(mode="json"),
        "output": clamped_output.model_dump(mode="json"),
        "h3_replay_window_seconds": window,
        "source_duration_seconds": str(duration),
    }
