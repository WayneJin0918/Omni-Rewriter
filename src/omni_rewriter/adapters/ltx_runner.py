"""Bounded subprocess adapter for the official LTX-2 distilled CLI."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Literal, Protocol

from pydantic import Field, model_validator

from ..errors import BackendConfigurationError, BackendResponseError, BackendTransportError
from ..models.common import StrictModel
from ..models.ltx import frames_for_duration
from ..models.request import RewriteRequest

_OFFICIAL_SPLIT = {
    "transformer": (
        "diffusion_models/ltx-2.5-22b-distilled-transformer-bf16.safetensors",
        "diffusion_models/*distilled*transformer*.safetensors",
    ),
    "text_encoder": (
        "text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors",
        "text_encoders/*gemma4*ltx-2.5*.safetensors",
    ),
    "video_vae": (
        "vae/ltx-2.5-video-vae-bf16.safetensors",
        "vae/*video-vae*.safetensors",
    ),
    "audio_vae": (
        "vae/ltx-2.5-audio-vae-bf16.safetensors",
        "vae/*audio-vae*.safetensors",
    ),
    "spatial_upsampler": (
        "latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors",
        "latent_upscale_models/*spatial-upscaler*.safetensors",
    ),
}


class LTXImageCondition(StrictModel):
    path: Path
    frame_index: int = Field(default=0, ge=0)
    strength: float = Field(default=0.8, ge=0, le=1)


class LTXVideoOptions(StrictModel):
    """Public distilled-CLI surface. Live generate remains unverified until a local run."""

    height: int = Field(default=512, gt=0)
    width: int = Field(default=768, gt=0)
    frame_rate: float = Field(default=24.0, gt=0, le=120)
    num_frames: int | None = Field(default=None, gt=0)
    seed: int = Field(default=10, ge=0)
    images: list[LTXImageCondition] = Field(default_factory=list, max_length=8)
    enhance_prompt: bool = False
    pipeline: Literal["distilled"] = "distilled"

    @model_validator(mode="after")
    def public_generate_bounds(self) -> "LTXVideoOptions":
        if self.height % 32 != 0 or self.width % 32 != 0:
            raise ValueError("LTX height and width must be divisible by 32")
        if self.num_frames is not None and self.num_frames % 8 != 1:
            raise ValueError("LTX num_frames must satisfy 8 * k + 1")
        return self


class LTXVideoResult(StrictModel):
    output: Path
    command: list[str]
    stdout: str = ""
    stderr: str = ""
    num_frames: int


class _SubprocessRun(Protocol):
    def __call__(
        self,
        args: list[str],
        *,
        cwd: Path | None,
        capture_output: bool,
        text: bool,
        timeout: float,
        check: bool,
    ) -> subprocess.CompletedProcess[str]: ...


class LTXVideoRunner:
    """Execute `python -m ltx_pipelines.distilled` with a fixed argument surface."""

    def __init__(
        self,
        checkpoint_root: str | Path,
        *,
        upstream_root: str | Path | None = None,
        python_executable: str = sys.executable,
        timeout: float = 3600.0,
        max_diagnostic_chars: int = 20_000,
        subprocess_run: _SubprocessRun = subprocess.run,
    ) -> None:
        if timeout <= 0:
            raise BackendConfigurationError("LTX subprocess timeout must be positive")
        if max_diagnostic_chars <= 0:
            raise BackendConfigurationError("LTX diagnostic bound must be positive")
        self.checkpoint_root = Path(checkpoint_root)
        self.upstream_root = Path(upstream_root) if upstream_root else None
        self.python_executable = python_executable
        self.timeout = timeout
        self.max_diagnostic_chars = max_diagnostic_chars
        self._subprocess_run = subprocess_run

    @classmethod
    def from_env(cls) -> "LTXVideoRunner":
        checkpoint = os.environ.get("OMNI_LTX_CHECKPOINT", "").strip()
        if not checkpoint:
            raise BackendConfigurationError(
                "Set OMNI_LTX_CHECKPOINT to the LTX-2.5 split checkpoint root "
                "(official layout: models/ltx-2.5)"
            )
        upstream = os.environ.get("OMNI_LTX_UPSTREAM", "").strip() or None
        return cls(checkpoint, upstream_root=upstream)

    def resolve_split_paths(self) -> dict[str, Path]:
        if not self.checkpoint_root.is_dir():
            raise BackendConfigurationError(
                f"LTX checkpoint root not found: {self.checkpoint_root}"
            )
        resolved: dict[str, Path] = {}
        for key, (exact, pattern) in _OFFICIAL_SPLIT.items():
            exact_path = self.checkpoint_root / exact
            if exact_path.is_file():
                resolved[key] = exact_path
                continue
            matches = sorted(self.checkpoint_root.glob(pattern))
            files = [path for path in matches if path.is_file()]
            if len(files) != 1:
                raise BackendConfigurationError(
                    f"LTX {key} checkpoint not found under {self.checkpoint_root} "
                    f"(expected {exact})"
                )
            resolved[key] = files[0]
        return resolved

    def resolve_num_frames(self, duration_seconds: object, options: LTXVideoOptions) -> int:
        if options.num_frames is not None:
            return options.num_frames
        from decimal import Decimal

        return frames_for_duration(Decimal(str(duration_seconds)), options.frame_rate)

    def build_command(
        self,
        prompt: str,
        output: str | Path,
        options: LTXVideoOptions,
        *,
        num_frames: int,
    ) -> list[str]:
        if not prompt.strip():
            raise BackendConfigurationError("LTX prompt must not be empty")
        paths = self.resolve_split_paths()
        command = [
            self.python_executable,
            "-m",
            "ltx_pipelines.distilled",
            "--transformer-path",
            str(paths["transformer"]),
            "--text-encoder-path",
            str(paths["text_encoder"]),
            "--video-vae-path",
            str(paths["video_vae"]),
            "--audio-vae-path",
            str(paths["audio_vae"]),
            "--spatial-upsampler-path",
            str(paths["spatial_upsampler"]),
            "--prompt",
            prompt,
            "--output-path",
            str(output),
            "--num-frames",
            str(num_frames),
            "--frame-rate",
            str(options.frame_rate),
            "--height",
            str(options.height),
            "--width",
            str(options.width),
            "--seed",
            str(options.seed),
        ]
        if options.enhance_prompt:
            command.append("--enhance-prompt")
        for image in options.images:
            command.extend(
                [
                    "--image",
                    str(image.path),
                    str(image.frame_index),
                    str(image.strength),
                ]
            )
        return command

    def images_for_request(
        self,
        request: RewriteRequest,
        *,
        num_frames: int,
        strength: float = 0.8,
    ) -> list[LTXImageCondition]:
        """Map i2va / l2va / fl2va / ref2va local images onto official --image flags."""

        images = [item for item in request.media if item.media_type.value == "image"]
        if not images:
            return []
        conditions: list[LTXImageCondition] = []
        last_frame = max(0, num_frames - 1)
        task = request.resolved_task.value
        for index, item in enumerate(images):
            uri = item.uri
            if uri.startswith("file://"):
                path = Path(uri.removeprefix("file://"))
            else:
                path = Path(uri)
            if task == "l2va" or (task == "fl2va" and index == 1):
                frame_index = last_frame
            else:
                frame_index = 0
            conditions.append(
                LTXImageCondition(path=path, frame_index=frame_index, strength=strength)
            )
        return conditions

    def run(
        self,
        prompt: str,
        output: str | Path,
        options: LTXVideoOptions,
        *,
        duration_seconds: object,
    ) -> LTXVideoResult:
        num_frames = self.resolve_num_frames(duration_seconds, options)
        for image in options.images:
            if not image.path.is_file():
                raise BackendConfigurationError(f"LTX conditioning image not found: {image.path}")
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = self.build_command(prompt, output_path, options, num_frames=num_frames)
        cwd = self.upstream_root if self.upstream_root is not None else Path.cwd()
        try:
            completed = self._subprocess_run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise BackendTransportError(f"LTX inference exceeded {self.timeout:g} seconds") from exc
        except OSError as exc:
            raise BackendTransportError(
                f"LTX inference could not start: {type(exc).__name__}"
            ) from exc
        stdout = self._bounded(completed.stdout)
        stderr = self._bounded(completed.stderr)
        if completed.returncode != 0:
            detail = stderr or stdout or "no diagnostic output"
            raise BackendResponseError(
                f"LTX inference exited with {completed.returncode}: {detail}"
            )
        if not output_path.is_file():
            raise BackendResponseError("LTX inference completed without creating output")
        return LTXVideoResult(
            output=output_path,
            command=command,
            stdout=stdout,
            stderr=stderr,
            num_frames=num_frames,
        )

    def _bounded(self, value: str | None) -> str:
        text = value or ""
        if len(text) <= self.max_diagnostic_chars:
            return text
        return text[-self.max_diagnostic_chars :]
