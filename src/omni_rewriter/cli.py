"""Typer command-line entry points."""

from __future__ import annotations

import asyncio
import json
import sys
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
from .service import expand as expand_service
from .service import validate_output, validation_error

app = typer.Typer(no_args_is_help=True, pretty_exceptions_show_locals=False)


class OutputFormat(StrEnum):
    JSON = "json"
    H3 = "h3"
    IMAGE = "image"


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
    if output is OutputFormat.H3 or output is OutputFormat.IMAGE:
        typer.echo(result.output.render())
        return
    payload = {
        "output": result.output.model_dump(mode="json"),
        "analysis": result.analysis.model_dump(mode="json"),
        "repairs": result.repairs,
        "run_id": result.run_id,
        "rendered_text": result.output.render(),
        # Backward-compatible alias for video PE consumers.
        "h3_text": result.output.render(),
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
        validated, _ = validate_output(payload)
    except (ValueError, TypeError) as exc:
        typer.echo(_json(validation_error(exc)), err=True)
        raise typer.Exit(1) from exc
    if output is OutputFormat.H3 or output is OutputFormat.IMAGE:
        typer.echo(validated.render())
    else:
        typer.echo(
            _json(
                {
                    "valid": True,
                    "output": validated.model_dump(mode="json"),
                    "rendered_text": validated.render(),
                    "h3_text": validated.render(),
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


def main() -> None:
    app()


if __name__ == "__main__":
    main()
