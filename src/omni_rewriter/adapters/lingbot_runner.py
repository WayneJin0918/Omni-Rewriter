"""Bounded subprocess adapter for the upstream LingBot-Video inference script."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Literal, Protocol

from pydantic import Field, model_validator

from ..errors import BackendConfigurationError, BackendResponseError, BackendTransportError
from ..models.common import StrictModel
from ..models.lingbot import LingBotCaption, LingBotVideoDescription


class LingBotVideoOptions(StrictModel):
    mode: Literal["t2i", "t2v", "ti2v"]
    backend: Literal["diffusers", "sglang"] = "diffusers"
    image: Path | None = None
    negative_prompt_json: Path | None = None
    height: int = Field(default=480, gt=0)
    width: int = Field(default=832, gt=0)
    num_frames: int | None = Field(default=None, gt=0)
    steps: int = Field(default=40, gt=0, le=200)
    guidance_scale: float = Field(default=3.0, ge=0, le=30)
    shift: float = Field(default=3.0, ge=0, le=30)
    seed: int = Field(default=42, ge=0)
    fps: int = Field(default=24, gt=0, le=120)
    run_refiner: bool = False
    refiner_output: Path | None = None
    refiner_steps: int = Field(default=8, gt=0, le=100)

    @model_validator(mode="after")
    def validate_mode_inputs(self) -> "LingBotVideoOptions":
        if self.mode == "ti2v" and self.image is None:
            raise ValueError("ti2v requires an image")
        if self.mode != "ti2v" and self.image is not None:
            raise ValueError("image is only valid for ti2v")
        if self.run_refiner != (self.refiner_output is not None):
            raise ValueError("run_refiner and refiner_output must be set together")
        return self


class LingBotVideoResult(StrictModel):
    output: Path
    refiner_output: Path | None = None
    command: list[str]
    stdout: str = ""
    stderr: str = ""


class _SubprocessRun(Protocol):
    def __call__(
        self,
        args: list[str],
        *,
        cwd: Path,
        capture_output: bool,
        text: bool,
        timeout: float,
        check: bool,
    ) -> subprocess.CompletedProcess[str]: ...


class LingBotVideoRunner:
    """Execute LingBot's local CLI with a fixed, validated argument surface."""

    def __init__(
        self,
        upstream_root: str | Path,
        model_dir: str | Path,
        *,
        python_executable: str = sys.executable,
        timeout: float = 3600.0,
        max_diagnostic_chars: int = 20_000,
        subprocess_run: _SubprocessRun = subprocess.run,
    ) -> None:
        if timeout <= 0:
            raise BackendConfigurationError("LingBot subprocess timeout must be positive")
        if max_diagnostic_chars <= 0:
            raise BackendConfigurationError("LingBot diagnostic bound must be positive")
        self.upstream_root = Path(upstream_root)
        self.model_dir = Path(model_dir)
        self.python_executable = python_executable
        self.timeout = timeout
        self.max_diagnostic_chars = max_diagnostic_chars
        self._subprocess_run = subprocess_run

    def build_command(
        self,
        prompt_json: str | Path,
        output: str | Path,
        options: LingBotVideoOptions,
    ) -> list[str]:
        script = self.upstream_root / "scripts" / "inference.py"
        command = [
            self.python_executable,
            str(script),
            "--backend",
            options.backend,
            "--model_dir",
            str(self.model_dir),
            "--mode",
            options.mode,
            "--prompt_json",
            str(prompt_json),
            "--output",
            str(output),
            "--height",
            str(options.height),
            "--width",
            str(options.width),
            "--steps",
            str(options.steps),
            "--guidance_scale",
            str(options.guidance_scale),
            "--shift",
            str(options.shift),
            "--seed",
            str(options.seed),
            "--fps",
            str(options.fps),
            "--transformer_dtype",
            "bf16",
            "--text_encoder_dtype",
            "bf16",
            "--vae_dtype",
            "fp32",
        ]
        if options.num_frames is not None:
            command.extend(["--num_frames", str(options.num_frames)])
        if options.image is not None:
            command.extend(["--image", str(options.image)])
        if options.negative_prompt_json is not None:
            command.extend(["--negative_prompt_json", str(options.negative_prompt_json)])
        if options.run_refiner:
            command.extend(
                [
                    "--run_refiner",
                    "--refiner_output",
                    str(options.refiner_output),
                    "--refiner_steps",
                    str(options.refiner_steps),
                ]
            )
        return command

    def run(
        self,
        caption: LingBotCaption,
        output: str | Path,
        options: LingBotVideoOptions,
    ) -> LingBotVideoResult:
        self._validate_runtime(caption, options)
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                suffix=".json",
                prefix=".lingbot-caption-",
                dir=output_path.parent,
                delete=False,
            ) as stream:
                stream.write(caption.model_dump_json(exclude_none=True, indent=2))
                prompt_path = Path(stream.name)
            command = self.build_command(prompt_path, output_path, options)
            try:
                completed = self._subprocess_run(
                    command,
                    cwd=self.upstream_root,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise BackendTransportError(
                    f"LingBot inference exceeded {self.timeout:g} seconds"
                ) from exc
            except OSError as exc:
                raise BackendTransportError(
                    f"LingBot inference could not start: {type(exc).__name__}"
                ) from exc
            stdout = self._bounded(completed.stdout)
            stderr = self._bounded(completed.stderr)
            if completed.returncode != 0:
                detail = stderr or stdout or "no diagnostic output"
                raise BackendResponseError(
                    f"LingBot inference exited with {completed.returncode}: {detail}"
                )
            if not output_path.is_file():
                raise BackendResponseError("LingBot inference completed without creating output")
            if options.refiner_output is not None and not options.refiner_output.is_file():
                raise BackendResponseError(
                    "LingBot refiner completed without creating refiner_output"
                )
            return LingBotVideoResult(
                output=output_path,
                refiner_output=options.refiner_output,
                command=command,
                stdout=stdout,
                stderr=stderr,
            )
        finally:
            if prompt_path is not None:
                prompt_path.unlink(missing_ok=True)

    def _validate_runtime(
        self,
        caption: LingBotCaption,
        options: LingBotVideoOptions,
    ) -> None:
        script = self.upstream_root / "scripts" / "inference.py"
        if not script.is_file():
            raise BackendConfigurationError(f"LingBot inference script not found: {script}")
        if not self.model_dir.is_dir():
            raise BackendConfigurationError(f"LingBot model directory not found: {self.model_dir}")
        is_video = isinstance(
            caption.caption.comprehensive_description,
            LingBotVideoDescription,
        )
        if (options.mode == "t2i") == is_video:
            raise BackendConfigurationError("LingBot mode does not match caption type")
        for path, label in (
            (options.image, "image"),
            (options.negative_prompt_json, "negative_prompt_json"),
        ):
            if path is not None and not path.is_file():
                raise BackendConfigurationError(f"LingBot {label} not found: {path}")

    def _bounded(self, value: str | None) -> str:
        text = value or ""
        if len(text) <= self.max_diagnostic_chars:
            return text
        return text[-self.max_diagnostic_chars :]
