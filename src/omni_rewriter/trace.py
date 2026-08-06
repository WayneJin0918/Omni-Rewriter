"""Redacted append-only JSONL traces for rewrite-agent runs."""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_SENSITIVE_KEY_RE = re.compile(r"(api[-_]?key|authorization|token|secret|password)", re.I)
_DATA_URI_RE = re.compile(r"data:[^,;\s]+(?:;[^,\s]*)?,[A-Za-z0-9+/=_%-]+", re.I)
_BEARER_RE = re.compile(r"Bearer\s+\S+", re.I)


def redact(value: Any) -> Any:
    """Recursively remove credentials and inline binary payloads."""

    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]" if _SENSITIVE_KEY_RE.search(str(key)) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    if isinstance(value, str):
        value = _DATA_URI_RE.sub("[REDACTED_DATA_URI]", value)
        return _BEARER_RE.sub("Bearer [REDACTED]", value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)


class JSONLTrace:
    """Concurrency-safe JSONL event sink."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = asyncio.Lock()

    async def write(self, event: str, **payload: Any) -> None:
        record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event": event,
            **redact(payload),
        }
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
        async with self._lock:
            await asyncio.to_thread(self._append, line)

    def _append(self, line: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(line)
