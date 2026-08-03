"""Optional FastAPI application factory."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from .agent import RewriteResult
from .config import Settings
from .models import RewriteRequest
from .service import expand as default_expand
from .service import validate_output, validation_error

Expander = Callable[[RewriteRequest, Settings], Awaitable[RewriteResult]]


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
            "HTTP server dependencies are not installed; install omni-writer[server]"
        ) from exc

    runtime_settings = settings or Settings.from_env()
    run_expand = expander or default_expand
    app = FastAPI(title="Omni-Writer", version="0.1.0")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/expand")
    async def expand_endpoint(request: RewriteRequest) -> dict[str, Any]:
        try:
            result = await run_expand(request, runtime_settings)
        except Exception as exc:
            from .errors import OmniWriterError

            if isinstance(exc, OmniWriterError):
                raise HTTPException(status_code=502, detail=str(exc)) from exc
            raise
        return {
            "output": result.output.model_dump(mode="json"),
            "analysis": result.analysis.model_dump(mode="json"),
            "repairs": result.repairs,
            "run_id": result.run_id,
            "h3_text": result.output.render(),
        }

    @app.post("/v1/validate")
    async def validate_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            output, _ = validate_output(payload)
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=422, detail=validation_error(exc)) from exc
        return {
            "valid": True,
            "output": output.model_dump(mode="json"),
            "h3_text": output.render(),
        }

    return app
