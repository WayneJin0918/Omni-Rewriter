from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import httpx
import pytest

from omni_rewriter.adapters import (
    LingBotRewriterClient,
    LingBotRewriterConfig,
    LingBotVideoOptions,
    LingBotVideoRunner,
)
from omni_rewriter.backends import ChatBackendConfig
from omni_rewriter.errors import (
    BackendConfigurationError,
    BackendResponseError,
    BackendTransportError,
)
from omni_rewriter.models import LingBotCaption, LingBotCaptionContent


def caption_content(*, video: bool) -> dict[str, Any]:
    description: str | dict[str, str]
    description = "A red cup rests on a wooden table."
    element: dict[str, Any] = {
        "name": "red cup",
        "description": "A small ceramic cup.",
        "location": "center",
        "relative_size": "medium",
        "shape_and_color": "cylindrical and red",
        "texture": "glossy ceramic",
        "appearance_details": "",
        "relationship": "on the table",
        "orientation": "upright",
    }
    if video:
        description = {
            "scene_content_description": "A red cup slides across a wooden table.",
            "camera_movement_description": "",
        }
        element["actions"] = [
            {"timestamp": "[0.0s - 5.0s]", "action": "slowly slides right"}
        ]
    return {
        "comprehensive_description": description,
        "camera_info": {
            "color": "Warm",
            "frame_size": "Close Up",
            "shot_type_angle": "Eye level",
            "lens_size": "Medium",
            "composition": "Center",
            "lighting": "Soft light",
            "lighting_type": "Daylight",
        },
        "world_knowledge": [],
        "prominent_elements": [element],
    }


def make_runner(
    tmp_path: Path,
    run: Any,
    *,
    timeout: float = 10,
    max_diagnostic_chars: int = 20_000,
) -> LingBotVideoRunner:
    upstream = tmp_path / "upstream"
    (upstream / "scripts").mkdir(parents=True)
    (upstream / "scripts" / "inference.py").write_text("# mock\n", encoding="utf-8")
    model = tmp_path / "model"
    model.mkdir()
    return LingBotVideoRunner(
        upstream,
        model,
        timeout=timeout,
        max_diagnostic_chars=max_diagnostic_chars,
        subprocess_run=run,
    )


def test_video_runner_invokes_bounded_upstream_cli(tmp_path: Path) -> None:
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append((args, kwargs))
        output = Path(args[args.index("--output") + 1])
        output.write_bytes(b"mp4")
        prompt = Path(args[args.index("--prompt_json") + 1])
        assert json.loads(prompt.read_text(encoding="utf-8"))["duration"] == 5
        return subprocess.CompletedProcess(args, 0, stdout="generated", stderr="")

    runner = make_runner(tmp_path, fake_run)
    output = tmp_path / "out" / "video.mp4"
    result = runner.run(
        LingBotCaption(caption=caption_content(video=True), duration=5),
        output,
        LingBotVideoOptions(mode="t2v", backend="sglang", steps=12),
    )

    assert result.output == output
    command, kwargs = calls[0]
    assert command[1].endswith("scripts/inference.py")
    assert command[command.index("--backend") + 1] == "sglang"
    assert command[command.index("--steps") + 1] == "12"
    assert kwargs["timeout"] == 10
    assert kwargs["check"] is False
    assert not list(output.parent.glob(".lingbot-caption-*.json"))


def test_video_runner_maps_failure_and_timeout(tmp_path: Path) -> None:
    def failed(args: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, 7, stdout="", stderr="x" * 100)

    runner = make_runner(tmp_path, failed, max_diagnostic_chars=12)
    caption = LingBotCaption(caption=caption_content(video=True), duration=5)
    options = LingBotVideoOptions(mode="t2v")
    with pytest.raises(BackendResponseError, match=r"exited with 7: x{12}$"):
        runner.run(caption, tmp_path / "failed.mp4", options)

    def timeout(args: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(args, 0.1)

    timed_runner = make_runner(tmp_path / "timed", timeout, timeout=0.1)
    with pytest.raises(BackendTransportError, match="exceeded"):
        timed_runner.run(caption, tmp_path / "timed.mp4", options)


def test_video_runner_rejects_mode_mismatch(tmp_path: Path) -> None:
    runner = make_runner(tmp_path, lambda *_args, **_kwargs: None)
    caption = LingBotCaption(caption=caption_content(video=False))
    with pytest.raises(BackendConfigurationError, match="caption type"):
        runner.run(caption, tmp_path / "bad.mp4", LingBotVideoOptions(mode="t2v"))


@pytest.mark.asyncio
async def test_two_stage_http_rewriter_uses_base_then_lora() -> None:
    requests: list[dict[str, Any]] = []
    mapped = json.dumps(caption_content(video=True))

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        requests.append(payload)
        content = "A detailed cup movement from zero to five seconds."
        if payload["model"] == "lingbot-map":
            content = mapped
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    config = LingBotRewriterConfig(
        expand_base=ChatBackendConfig(
            base_url="http://rewriter.test/v1",
            model="lingbot-expand",
            retries=0,
            temperature=0,
        ),
        map_lora=ChatBackendConfig(
            base_url="http://rewriter.test/v1",
            model="lingbot-map",
            retries=0,
            temperature=0,
        ),
    )
    adapter = LingBotRewriterClient(
        config,
        expand_client=http_client,
        map_client=http_client,
    )
    result = await adapter.rewrite("A cup slides right.", mode="t2v", duration=5)

    assert result.caption.duration == 5
    assert [request["model"] for request in requests] == ["lingbot-expand", "lingbot-map"]
    assert "response_format" not in requests[0]
    assert requests[1]["response_format"]["type"] == "json_schema"
    await adapter.aclose()
    await http_client.aclose()


def test_rewriter_requires_distinct_base_and_mapping_stage() -> None:
    endpoint = ChatBackendConfig(base_url="http://same.test/v1", model="same")
    with pytest.raises(ValueError, match="different endpoints or model"):
        LingBotRewriterConfig(expand_base=endpoint, map_lora=endpoint)

    assert LingBotCaptionContent.model_validate(caption_content(video=False))
