"""Smoke tests for the multi-file PE validator used by the GitHub Action."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_pe_files.py"


def _load():
    spec = importlib.util.spec_from_file_location("validate_pe_files", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_validate_pe_files_ok() -> None:
    module = _load()
    assert module.main([str(ROOT / "tests/fixtures/t2va_kite.json")]) == 0


def test_validate_pe_files_missing() -> None:
    module = _load()
    assert module.main([str(ROOT / "tests/fixtures/does-not-exist.json")]) == 1
