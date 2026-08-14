"""Typer command-line entry points."""

from __future__ import annotations

import asyncio
import json
import sys
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Any

try:
    import typer
except ImportError as exc:  # pragma: no cover - exercised in minimal installs
    raise RuntimeError("CLI dependencies are not installed; install omni-rewriter[cli]") from exc

from .config import Settings
from .errors import OmniRewriterError
from .evaluator import BasicEvaluator
from .models import RewriteRequest
from .models.observation import VideoObservation
from .service import expand as expand_service
from .service import render_output, validate_output, validation_error

app = typer.Typer(no_args_is_help=True, pretty_exceptions_show_locals=False)


class OutputFormat(StrEnum):
    JSON = "json"
    H3 = "h3"
    IMAGE = "image"
    SEEDANCE = "seedance"
    LTX = "ltx"


def _read_json(source: str) -> dict[str, Any]:
    try:
        raw = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(f"cannot read JSON input: {exc}") from exc
    if not isinstance(value, dict):
        raise typer.BadParameter("JSON input must be an object")
    return value


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


@app.command("expand")
def expand_command(
    source: str = typer.Argument("-", help="JSON file, or - for stdin"),
    output: OutputFormat = typer.Option(OutputFormat.JSON, "--output", "-o"),
) -> None:
    """Expand a RewriteRequest through the configured writer backend."""

    try:
        request = RewriteRequest.model_validate(_read_json(source))
        result = asyncio.run(expand_service(request, Settings.from_env()))
    except (ValueError, OmniRewriterError) as exc:
        typer.echo(_json(validation_error(exc)), err=True)
        raise typer.Exit(1) from exc
    rendered = render_output(result.output, request)
    if output in {OutputFormat.H3, OutputFormat.IMAGE, OutputFormat.SEEDANCE, OutputFormat.LTX}:
        typer.echo(rendered)
        return
    payload = {
        "output": result.output.model_dump(mode="json"),
        "analysis": result.analysis.model_dump(mode="json"),
        "repairs": result.repairs,
        "run_id": result.run_id,
        "rendered_text": rendered,
        # Backward-compatible alias for video PE consumers.
        "h3_text": rendered,
    }
    typer.echo(_json(payload))


@app.command("validate")
def validate_command(
    source: str = typer.Argument("-", help="JSON file, or - for stdin"),
    output: OutputFormat = typer.Option(OutputFormat.JSON, "--output", "-o"),
) -> None:
    """Validate an output object or a request/output envelope."""

    payload = _read_json(source)
    try:
        validated, request = validate_output(payload)
    except (ValueError, TypeError) as exc:
        typer.echo(_json(validation_error(exc)), err=True)
        raise typer.Exit(1) from exc
    rendered = render_output(validated, request)
    if output in {OutputFormat.H3, OutputFormat.IMAGE, OutputFormat.SEEDANCE, OutputFormat.LTX}:
        typer.echo(rendered)
    else:
        typer.echo(
            _json(
                {
                    "valid": True,
                    "output": validated.model_dump(mode="json"),
                    "rendered_text": rendered,
                    "h3_text": rendered,
                }
            )
        )


@app.command("eval")
def eval_command(
    source: str = typer.Argument("-", help="JSON file, or - for stdin"),
    manifest: bool = typer.Option(False, "--manifest", help="Read a JSONL manifest"),
) -> None:
    """Run the current evaluator interface."""

    evaluator = BasicEvaluator()
    if manifest:
        if source == "-":
            records: list[dict[str, Any]] = []
            try:
                for line in sys.stdin:
                    if line.strip():
                        value = json.loads(line)
                        if not isinstance(value, dict):
                            raise TypeError("manifest record must be a JSON object")
                        records.append(value)
            except (json.JSONDecodeError, TypeError) as exc:
                raise typer.BadParameter(f"cannot read JSONL manifest: {exc}") from exc
            result = evaluator.evaluate_manifest(records)
        else:
            try:
                result = evaluator.evaluate_manifest(source)
            except OSError as exc:
                raise typer.BadParameter(f"cannot read JSONL manifest: {exc}") from exc
    else:
        result = evaluator.evaluate(_read_json(source))
    typer.echo(_json(result))
    if not result["valid"]:
        raise typer.Exit(1)


def _load_observation(path: Path) -> VideoObservation:
    payload = _read_json(str(path))
    raw = payload.get("observation", payload)
    if not isinstance(raw, dict):
        raise typer.BadParameter("observation JSON must be an object")
    return VideoObservation.model_validate(raw)


@app.command("reconstruct")
def reconstruct_command(
    source: str | None = typer.Argument(None, help="Local video path (not inlined into expand)"),
    from_observation: Path | None = typer.Option(
        None,
        "--from-observation",
        help="VideoObservation JSON, or an envelope with an observation key",
    ),
    pack_only: bool = typer.Option(False, "--pack-only", help="Stop after ffmpeg evidence pack"),
    pack_dir: Path | None = typer.Option(
        None, "--pack-dir", help="Directory for JPEG/wav evidence"
    ),
    max_duration: float = typer.Option(
        45.0, "--max-duration", help="Reject clips longer than this many seconds"
    ),
    max_keyframes: int = typer.Option(16, "--max-keyframes", help="Max JPEG stills for the VLM"),
    step_seconds: float = typer.Option(0.5, "--step-seconds", help="Keyframe spacing before cap"),
    output: OutputFormat = typer.Option(OutputFormat.JSON, "--output", "-o"),
) -> None:
    """Observe a local clip (or a saved observation) and emit validated H3 t2va PE.

    Expand ≠ generate. The source mp4 is never sent through ``expand``.
    """

    from tempfile import TemporaryDirectory

    from .reconstruct.evidence import EvidencePack, EvidencePackConfig
    from .reconstruct.service import reconstruct, result_payload

    if output in {OutputFormat.IMAGE, OutputFormat.SEEDANCE, OutputFormat.LTX}:
        raise typer.BadParameter("reconstruct v1 emits H3 t2va; use --output json or h3")
    if pack_only and from_observation is not None:
        raise typer.BadParameter("--pack-only cannot be combined with --from-observation")
    if pack_only and source is None:
        raise typer.BadParameter("--pack-only requires a local video path")
    if pack_only and pack_dir is None:
        raise typer.BadParameter("--pack-only requires --pack-dir so frames are kept")
    if source is None and from_observation is None:
        raise typer.BadParameter("provide a video path or --from-observation")

    observation = None
    tmp: TemporaryDirectory[str] | None = None
    active_pack_dir = pack_dir
    try:
        if from_observation is not None:
            observation = _load_observation(from_observation)
        if source is not None and active_pack_dir is None:
            tmp = TemporaryDirectory(prefix="omni-reconstruct-")
            active_pack_dir = Path(tmp.name)
        result = asyncio.run(
            reconstruct(
                source=Path(source) if source else None,
                observation=observation,
                pack_dir=active_pack_dir,
                pack_only=pack_only,
                pack_config=EvidencePackConfig(
                    max_duration_seconds=Decimal(str(max_duration)),
                    max_keyframes=max_keyframes,
                    step_seconds=Decimal(str(step_seconds)),
                ),
            )
        )
    except (ValueError, OmniRewriterError) as exc:
        typer.echo(_json(validation_error(exc)), err=True)
        raise typer.Exit(1) from exc
    finally:
        if tmp is not None:
            tmp.cleanup()

    if pack_only:
        assert isinstance(result, EvidencePack)
        typer.echo(_json(result.summary()))
        return
    from .reconstruct.service import ReconstructResult

    assert isinstance(result, ReconstructResult)
    if output is OutputFormat.H3:
        typer.echo(result.rewrite.output.render())
        return
    payload = result_payload(result)
    if tmp is not None:
        payload.pop("evidence", None)
    typer.echo(_json(payload))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
