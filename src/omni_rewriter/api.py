"""Optional FastAPI application factory."""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from typing import Any

from .agent import RewriteResult
from .config import Settings
from .errors import OmniRewriterError
from .models import RewriteRequest
from .models.observation import VideoObservation
from .service import expand as default_expand
from .service import render_output, validate_output, validation_error

Expander = Callable[[RewriteRequest, Settings], Awaitable[RewriteResult]]


def _api_allow_local_media() -> bool:
    """HTTP expand denies local paths unless OMNI_WRITER_ALLOW_LOCAL_MEDIA is set true."""

    raw = os.environ.get("OMNI_WRITER_ALLOW_LOCAL_MEDIA")
    if raw is None:
        return False
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def create_app(
    settings: Settings | None = None,
    *,
    expander: Expander | None = None,
) -> Any:
    """Create the HTTP app, with an actionable error in core-only installs."""

    try:
        from fastapi import FastAPI, HTTPException
    except ImportError as exc:  # pragma: no cover - depends on installation extras
        raise RuntimeError(
            "HTTP server dependencies are not installed; install omni-rewriter[server]"
        ) from exc

    runtime_settings = settings or Settings.from_env()
    api_settings = runtime_settings.model_copy(
        update={"allow_local_media": _api_allow_local_media()}
    )
    run_expand = expander or default_expand
    app = FastAPI(title="Omni-Rewriter", version="0.1.0")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/expand")
    async def expand_endpoint(request: RewriteRequest) -> dict[str, Any]:
        try:
            result = await run_expand(request, api_settings)
        except Exception as exc:
            from .errors import OmniRewriterError

            if isinstance(exc, OmniRewriterError):
                raise HTTPException(status_code=502, detail=str(exc)) from exc
            raise
        rendered = render_output(result.output, request)
        return {
            "output": result.output.model_dump(mode="json"),
            "analysis": result.analysis.model_dump(mode="json"),
            "repairs": result.repairs,
            "run_id": result.run_id,
            "rendered_text": rendered,
            "h3_text": rendered,
        }

    @app.post("/v1/validate")
    async def validate_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            output, request = validate_output(payload)
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=422, detail=validation_error(exc)) from exc
        rendered = render_output(output, request)
        return {
            "valid": True,
            "output": output.model_dump(mode="json"),
            "rendered_text": rendered,
            "h3_text": rendered,
        }

    @app.post("/v1/reconstruct")
    async def reconstruct_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        """Observation → H3 t2va PE. Local mp4 stays on the CLI; do not POST a clip."""

        from .reconstruct.service import reconstruct, result_payload

        raw = payload.get("observation", payload)
        if not isinstance(raw, dict):
            raise HTTPException(
                status_code=422,
                detail=validation_error(ValueError("observation must be a JSON object")),
            )
        try:
            observation = VideoObservation.model_validate(raw)
            result = await reconstruct(observation=observation, settings=api_settings)
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=422, detail=validation_error(exc)) from exc
        except OmniRewriterError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        from .reconstruct.service import ReconstructResult

        assert isinstance(result, ReconstructResult)
        return result_payload(result)

    return app
