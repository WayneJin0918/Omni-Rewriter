from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from omni_rewriter.adapters import LTXImageCondition, LTXVideoOptions, LTXVideoRunner
from omni_rewriter.errors import BackendConfigurationError, BackendResponseError
from omni_rewriter.models import MediaReference, MediaRole, MediaType, RewriteRequest, TaskType


def _touch_split(root: Path) -> None:
    files = (
        "diffusion_models/ltx-2.5-22b-distilled-transformer-bf16.safetensors",
        "text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors",
        "vae/ltx-2.5-video-vae-bf16.safetensors",
        "vae/ltx-2.5-audio-vae-bf16.safetensors",
        "latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors",
    )
    for relative in files:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"ckpt")


def test_ltx_runner_builds_official_distilled_cli(tmp_path: Path) -> None:
    checkpoint = tmp_path / "ltx-2.5"
    _touch_split(checkpoint)
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append((args, kwargs))
        Path(args[args.index("--output-path") + 1]).write_bytes(b"mp4")
        return subprocess.CompletedProcess(args, 0, stdout="ok", stderr="")

    runner = LTXVideoRunner(checkpoint, subprocess_run=fake_run, timeout=12)
    output = tmp_path / "out" / "clip.mp4"
    result = runner.run(
        "A potter throws a clay bowl on a spinning wheel.",
        output,
        LTXVideoOptions(seed=42),
        duration_seconds="5",
    )
    command, kwargs = calls[0]
    assert command[1:3] == ["-m", "ltx_pipelines.distilled"]
    assert command[command.index("--num-frames") + 1] == "121"
    assert command[command.index("--seed") + 1] == "42"
    assert "--enhance-prompt" not in command
    assert kwargs["timeout"] == 12
    assert result.num_frames == 121
    assert result.output == output


def test_ltx_runner_maps_i2va_image_flag(tmp_path: Path) -> None:
    checkpoint = tmp_path / "ltx-2.5"
    _touch_split(checkpoint)
    still = tmp_path / "face.png"
    still.write_bytes(b"png")
    request = RewriteRequest(
        prompt="Keep this face.",
        duration_seconds="5",
        task=TaskType.I2VA,
        media=[
            MediaReference(
                media_type=MediaType.IMAGE,
                role=MediaRole.FIRST_FRAME,
                uri=str(still),
                name="face",
            )
        ],
        metadata={"video_pe_profile": "ltx"},
    )
    runner = LTXVideoRunner(checkpoint)
    images = runner.images_for_request(request, num_frames=121)
    assert images == [LTXImageCondition(path=still, frame_index=0, strength=0.8)]
    command = runner.build_command(
        "A woman looks into camera.",
        tmp_path / "out.mp4",
        LTXVideoOptions(images=images),
        num_frames=121,
    )
    image_at = command.index("--image")
    assert command[image_at : image_at + 4] == ["--image", str(still), "0", "0.8"]


def test_ltx_runner_maps_failure(tmp_path: Path) -> None:
    checkpoint = tmp_path / "ltx-2.5"
    _touch_split(checkpoint)

    def failed(args: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, 3, stdout="", stderr="oom")

    runner = LTXVideoRunner(checkpoint, subprocess_run=failed, max_diagnostic_chars=8)
    with pytest.raises(BackendResponseError, match="exited with 3: oom"):
        runner.run("prompt", tmp_path / "x.mp4", LTXVideoOptions(), duration_seconds="5")


def test_ltx_runner_requires_checkpoint(tmp_path: Path) -> None:
    runner = LTXVideoRunner(tmp_path / "missing")
    with pytest.raises(BackendConfigurationError, match="checkpoint root not found"):
        runner.resolve_split_paths()
