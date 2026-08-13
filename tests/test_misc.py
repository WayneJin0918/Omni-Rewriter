from __future__ import annotations

import json
from pathlib import Path

import pytest

from omni_rewriter.config import DEFAULT_WRITER_MODEL, Settings
from omni_rewriter.errors import BackendConfigurationError
from omni_rewriter.service import validate_output, validation_error
from omni_rewriter.trace import JSONLTrace, redact


def test_settings_default_writer_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OMNI_WRITER_BACKEND_MODEL", raising=False)
    monkeypatch.delenv("OMNI_WRITER_MODEL", raising=False)
    assert DEFAULT_WRITER_MODEL == "Qwen/Qwen3.6-35B-A3B"
    assert Settings().backend_model == DEFAULT_WRITER_MODEL
    assert Settings.from_env().backend_model == DEFAULT_WRITER_MODEL


def test_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OMNI_WRITER_BACKEND_BASE_URL", "http://writer.test/v1")
    monkeypatch.setenv("OMNI_WRITER_BACKEND_MODEL", "local-qwen")
    monkeypatch.setenv("OMNI_WRITER_ENABLE_THINKING", "true")
    monkeypatch.setenv("OMNI_WRITER_MAX_REPAIRS", "3")
    monkeypatch.setenv("MINIMAX_API_KEY", "secret")
    monkeypatch.delenv("OMNI_WRITER_H3_BASE_URL", raising=False)
    settings = Settings.from_env()
    assert settings.chat_backend_config().model == "local-qwen"
    assert settings.chat_backend_config().enable_thinking is True
    assert settings.h3_client_config().base_url == "http://127.0.0.1:30000"
    assert settings.minimax_client_config().api_key.get_secret_value() == "secret"


def test_settings_minimax_requires_key() -> None:
    with pytest.raises(BackendConfigurationError, match="MINIMAX_API_KEY"):
        Settings(minimax_api_key=None).minimax_client_config()


def test_validate_output_envelope(base_output: dict[str, object]) -> None:
    output, request = validate_output(
        {
            "request": {"prompt": "A kite rises.", "duration_seconds": 6},
            "output": base_output,
        }
    )
    assert request is not None
    assert output.duration_seconds == request.duration_seconds
    with pytest.raises(ValueError, match="object-valued request"):
        validate_output({"request": "bad", "output": base_output})
    with pytest.raises(ValueError, match="JSON object"):
        validate_output(
            {
                "request": {"prompt": "A kite rises.", "duration_seconds": 6},
                "output": "bad",
            }
        )


def test_validation_error_for_plain_exception() -> None:
    value = validation_error(ValueError("bad value"))
    assert value == {
        "valid": False,
        "errors": [{"type": "ValueError", "msg": "bad value"}],
    }


def test_trace_redaction() -> None:
    assert redact(
        {
            "api_key": "secret",
            "nested": ["Bearer token", "data:image/png;base64,AAAA"],
            "value": 1,
        }
    ) == {
        "api_key": "[REDACTED]",
        "nested": ["Bearer [REDACTED]", "[REDACTED_DATA_URI]"],
        "value": 1,
    }


@pytest.mark.asyncio
async def test_jsonl_trace_write(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "trace.jsonl"
    trace = JSONLTrace(path)
    await trace.write("state", token="hidden", status="ok")
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["event"] == "state"
    assert record["token"] == "[REDACTED]"
    assert record["status"] == "ok"
