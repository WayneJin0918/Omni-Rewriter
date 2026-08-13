from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from omni_rewriter.api import create_app
from omni_rewriter.backends import ScriptedBackend
from omni_rewriter.cli import app
from omni_rewriter.config import Settings
from omni_rewriter.models.observation import VideoObservation
from omni_rewriter.reconstruct.evidence import EvidencePackError, build_evidence_pack
from omni_rewriter.reconstruct.service import observation_to_request, reconstruct
from omni_rewriter.service import validate_output

ROOT = Path(__file__).resolve().parents[1]
KITE_ENVELOPE = ROOT / "docs/design/examples/observation_kite.json"
FFMPEG = shutil.which("ffmpeg") and shutil.which("ffprobe")


def _observation() -> dict[str, Any]:
    return json.loads(KITE_ENVELOPE.read_text(encoding="utf-8"))["observation"]


def _patch_expand_backend(monkeypatch: pytest.MonkeyPatch, responses: list[str]) -> ScriptedBackend:
    backend = ScriptedBackend(responses)
    monkeypatch.setattr("omni_rewriter.service.OpenAICompatibleBackend", lambda _config: backend)
    return backend


def _make_clip(path: Path, seconds: int = 6) -> Path:
    import subprocess

    completed = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"testsrc=size=640x360:rate=24:duration={seconds}",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=880:duration={seconds}",
            "-pix_fmt",
            "yuv420p",
            "-c:v",
            "mpeg4",
            "-c:a",
            "aac",
            "-shortest",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        pytest.skip(f"ffmpeg cannot synthesize a clip: {completed.stderr[-300:]}")
    return path


def test_design_example_validates() -> None:
    envelope = json.loads(KITE_ENVELOPE.read_text(encoding="utf-8"))
    VideoObservation.model_validate(envelope["observation"])
    output, request = validate_output(envelope)
    assert request is not None
    assert output.task.value == "t2va"
    assert request.metadata.get("reconstruct") == "v1-t2va"


def test_observation_to_request_is_t2va_without_media() -> None:
    observation = VideoObservation.model_validate(_observation())
    request = observation_to_request(observation)
    assert request.resolved_task.value == "t2va"
    assert request.media == []
    assert request.video_pe_profile == "h3"
    assert "Hold the line!" in request.prompt


@pytest.mark.asyncio
async def test_reconstruct_from_observation(
    monkeypatch: pytest.MonkeyPatch,
    analysis_output: dict[str, Any],
    base_output: dict[str, Any],
) -> None:
    _patch_expand_backend(
        monkeypatch,
        [json.dumps(analysis_output), json.dumps(base_output)],
    )
    result = await reconstruct(observation=VideoObservation.model_validate(_observation()))
    assert result.pack is None
    assert result.rewrite.output.task.value == "t2va"
    assert result.request.media == []


@pytest.mark.skipif(not FFMPEG, reason="ffmpeg/ffprobe required for evidence packs")
def test_evidence_pack_does_not_copy_source_mp4(tmp_path: Path) -> None:
    clip = _make_clip(tmp_path / "clip.mp4")
    pack = build_evidence_pack(clip, tmp_path / "pack")
    assert pack.probe.has_video is True
    assert pack.probe.has_audio is True
    assert 2 <= len(pack.frames) <= 16
    assert all(frame.path.suffix == ".jpg" for frame in pack.frames)
    assert pack.audio_wav is not None and pack.audio_wav.is_file()
    assert not any(path.suffix == ".mp4" for path in (tmp_path / "pack").rglob("*"))
    assert pack.probe.duration_seconds <= 6.1


@pytest.mark.skipif(not FFMPEG, reason="ffmpeg/ffprobe required for evidence packs")
def test_evidence_pack_rejects_overlong_clip(tmp_path: Path) -> None:
    from omni_rewriter.reconstruct.evidence import EvidencePackConfig

    clip = _make_clip(tmp_path / "long.mp4", seconds=2)
    with pytest.raises(EvidencePackError, match="cap"):
        build_evidence_pack(
            clip,
            tmp_path / "pack",
            EvidencePackConfig(max_duration_seconds="1"),
        )


@pytest.mark.asyncio
@pytest.mark.skipif(not FFMPEG, reason="ffmpeg/ffprobe required for evidence packs")
async def test_observe_repairs_invalid_json(tmp_path: Path) -> None:
    clip = _make_clip(tmp_path / "clip.mp4")
    pack = build_evidence_pack(clip, tmp_path / "pack")
    from omni_rewriter.models.observation import format_timecode
    from omni_rewriter.reconstruct.observe import observe_pack

    payload = _observation()
    payload["duration_seconds"] = str(pack.probe.duration_seconds)
    payload["shots"][-1]["end"] = format_timecode(pack.probe.duration_seconds)
    backend = ScriptedBackend(["{}", json.dumps(payload)])
    observation = await observe_pack(pack, backend, max_repairs=1)
    assert observation.duration_seconds == pack.probe.duration_seconds
    assert len(backend.calls) == 2


@pytest.mark.asyncio
@pytest.mark.skipif(not FFMPEG, reason="ffmpeg/ffprobe required for evidence packs")
async def test_reconstruct_video_observe_then_expand(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    analysis_output: dict[str, Any],
    base_output: dict[str, Any],
) -> None:
    clip = _make_clip(tmp_path / "clip.mp4")
    pack = build_evidence_pack(clip, tmp_path / "seed-pack")
    from omni_rewriter.models.observation import format_timecode

    observation_payload = _observation()
    observation_payload["duration_seconds"] = str(pack.probe.duration_seconds)
    observation_payload["shots"][-1]["end"] = format_timecode(pack.probe.duration_seconds)
    observation = VideoObservation.model_validate(observation_payload)
    observe_backend = ScriptedBackend([json.dumps(observation.model_dump(mode="json"))])
    _patch_expand_backend(
        monkeypatch,
        [json.dumps(analysis_output), json.dumps(base_output)],
    )
    result = await reconstruct(
        source=clip,
        pack_dir=tmp_path / "pack",
        backend=observe_backend,
    )
    assert result.pack is not None
    assert result.rewrite.output.task.value == "t2va"
    assert result.request.metadata.get("aspect_ratio") == "16:9"
    assert len(observe_backend.calls) == 1
    user = observe_backend.calls[0][1]
    assert isinstance(user["content"], list)
    assert user["content"][0]["type"] == "text"
    assert any(part.get("type") == "image_url" for part in user["content"])


def test_cli_pack_only(tmp_path: Path) -> None:
    if not FFMPEG:
        pytest.skip("ffmpeg/ffprobe required for evidence packs")
    clip = _make_clip(tmp_path / "clip.mp4")
    pack_dir = tmp_path / "kept"
    response = CliRunner().invoke(
        app,
        ["reconstruct", str(clip), "--pack-only", "--pack-dir", str(pack_dir)],
    )
    assert response.exit_code == 0, response.stderr
    payload = json.loads(response.stdout)
    assert payload["probe"]["has_video"] is True
    assert Path(payload["frames"][0]["path"]).is_file()


def test_cli_from_observation(
    monkeypatch: pytest.MonkeyPatch,
    analysis_output: dict[str, Any],
    base_output: dict[str, Any],
) -> None:
    async def fake_reconstruct(**_: Any) -> Any:
        from omni_rewriter.agent import AnalysisPlan, RewriteResult
        from omni_rewriter.models import BaseRewrite
        from omni_rewriter.reconstruct.service import ReconstructResult

        observation = VideoObservation.model_validate(_observation())
        request = observation_to_request(observation)
        return ReconstructResult(
            observation=observation,
            request=request,
            rewrite=RewriteResult(
                output=BaseRewrite.model_validate(base_output),
                analysis=AnalysisPlan.model_validate(analysis_output),
                repairs=0,
                run_id="recon-1",
            ),
        )

    monkeypatch.setattr("omni_rewriter.reconstruct.service.reconstruct", fake_reconstruct)
    response = CliRunner().invoke(
        app,
        ["reconstruct", "--from-observation", str(KITE_ENVELOPE)],
    )
    assert response.exit_code == 0, response.stderr
    payload = json.loads(response.stdout)
    assert payload["run_id"] == "recon-1"
    assert payload["request"]["task"] == "t2va"
    assert "media" in payload["request"]


def test_api_reconstruct_from_observation(
    monkeypatch: pytest.MonkeyPatch,
    analysis_output: dict[str, Any],
    base_output: dict[str, Any],
) -> None:
    _patch_expand_backend(
        monkeypatch,
        [json.dumps(analysis_output), json.dumps(base_output)],
    )
    client = TestClient(create_app(Settings()))
    response = client.post("/v1/reconstruct", json={"observation": _observation()})
    assert response.status_code == 200
    body = response.json()
    assert body["output"]["task"] == "t2va"
    assert body["observation"]["shots"][0]["index"] == 1
