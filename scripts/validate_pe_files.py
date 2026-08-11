#!/usr/bin/env python3
"""Validate one or more PE JSON envelopes for CI / GitHub Action use.

Accepts files and shell globs. Each JSON must be a RewriteOutput object or a
``{"request": ..., "output": ...}`` envelope. Exit code 1 if any file fails.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from omni_rewriter.service import validate_output, validation_error


def _expand(patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for pattern in patterns:
        path = Path(pattern)
        matches = sorted(Path().glob(pattern)) if any(ch in pattern for ch in "*?[") else [path]
        if not matches and not path.exists():
            raise FileNotFoundError(f"no files matched: {pattern}")
        for match in matches:
            resolved = match.resolve()
            if resolved in seen or not match.is_file():
                continue
            seen.add(resolved)
            files.append(match)
    return files


def _validate_file(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"path": str(path), "valid": False, "errors": [{"msg": str(exc)}]}
    if not isinstance(payload, dict):
        return {
            "path": str(path),
            "valid": False,
            "errors": [{"msg": "JSON root must be an object"}],
        }
    try:
        validate_output(payload)
    except (ValueError, TypeError) as exc:
        return {"path": str(path), **validation_error(exc)}
    return {"path": str(path), "valid": True}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "patterns",
        nargs="+",
        help="PE JSON files or globs (e.g. tests/fixtures/**/*.json)",
    )
    parser.add_argument(
        "--fail-fast",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Stop on the first failure (default: true)",
    )
    args = parser.parse_args(argv)

    try:
        files = _expand(args.patterns)
    except FileNotFoundError as exc:
        print(json.dumps({"valid": False, "errors": [{"msg": str(exc)}]}, indent=2), file=sys.stderr)
        return 1

    if not files:
        print(
            json.dumps({"valid": False, "errors": [{"msg": "no files to validate"}]}, indent=2),
            file=sys.stderr,
        )
        return 1

    results: list[dict[str, Any]] = []
    failed = 0
    for path in files:
        result = _validate_file(path)
        results.append(result)
        status = "ok" if result["valid"] else "FAIL"
        print(f"[{status}] {path}", flush=True)
        if not result["valid"]:
            failed += 1
            print(json.dumps(result, indent=2, ensure_ascii=False), file=sys.stderr)
            if args.fail_fast:
                break

    summary = {
        "valid": failed == 0,
        "checked": len(results),
        "failed": failed,
        "results": results,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
