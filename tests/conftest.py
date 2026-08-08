from __future__ import annotations

import ipaddress
import socket
from typing import Any

import pytest


@pytest.fixture(autouse=True)
def resolve_test_hosts_as_public(monkeypatch: pytest.MonkeyPatch) -> None:
    """Map unresolvable *.test mock hosts to a public IP for adapter SSRF checks."""

    real_getaddrinfo = socket.getaddrinfo

    def fake_getaddrinfo(
        host: str | bytes | None,
        port: str | int | None,
        family: int = 0,
        type: int = 0,
        proto: int = 0,
        flags: int = 0,
    ) -> list[tuple[Any, ...]]:
        hostname = host.decode() if isinstance(host, bytes) else (host or "")
        try:
            address = ipaddress.ip_address(hostname)
        except ValueError:
            address = None
        if address is not None or hostname in {"localhost"} or hostname.endswith(".local"):
            return real_getaddrinfo(host, port, family, type, proto, flags)
        port_num = (
            int(port) if isinstance(port, int) or (isinstance(port, str) and port.isdigit()) else 0
        )
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port_num))]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)


@pytest.fixture
def base_output() -> dict[str, Any]:
    return {
        "task": "t2va",
        "duration_seconds": "6",
        "integrated_multimodal_description": (
            "[Shot 1] A paper kite rises above a quiet hill. "
            "[Shot 2] At 00:03.000, it turns toward warm sunset light."
        ),
        "overall_soundscape": "Soft wind and distant grass movement.",
        "non_diegetic_music": "A restrained two-note string motif.",
    }


@pytest.fixture
def analysis_output() -> dict[str, Any]:
    return {
        "intent": "Show one clear upward movement.",
        "observable_media_facts": [],
        "timing_and_motion": ["The turn happens halfway through."],
        "audio_and_dialogue": ["No dialogue."],
        "continuity_risks": [],
        "constraints": ["Keep the kite visible."],
    }


@pytest.fixture
def ref_output() -> dict[str, Any]:
    return {
        "duration_seconds": "6",
        "subject_definitions": "<Subject 1> A small red paper kite with a white tail.",
        "summary": "[reference generation] A kite crosses a calm evening sky.",
        "retention_analysis": (
            "<Subject 1>: fully_preserved - Keep its red paper body and white tail."
        ),
        "detailed_description": (
            "[Shot 1] <Subject 1> climbs through a pale sky. "
            "[Shot 2] At 00:03.000, <Subject 1> banks gently left."
        ),
        "overall_soundscape": "Light wind passes over the hill.",
        "non_diegetic_music": "Sparse plucked strings.",
    }


@pytest.fixture
def seedream_output() -> dict[str, Any]:
    return {
        "task": "t2i",
        "profile": "seedream",
        "prompt": (
            "Rain-soaked neon sushi storefront at night, wet asphalt reflections, "
            "horizontal poster composition, title text exactly “Summer Special”, "
            "cool cyan and magenta lights, no people."
        ),
        "ratio": "16:9",
    }


@pytest.fixture
def qwen_edit_output() -> dict[str, Any]:
    return {
        "task": "image_edit",
        "profile": "qwen_image_edit",
        "prompt": (
            "Keep the woman from image 1, change the dress to deep emerald silk, "
            "preserve face and pose."
        ),
        "ratio": "[image 1]",
    }


@pytest.fixture
def png_bytes() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * 24
