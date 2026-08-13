#!/usr/bin/env python3
"""Batch reconstruct → optional H3 replay for SOURCE|REPLAY promo demos.

Expand ≠ generate. Does not commit mp4. H3 generate stays on the public 4–15s window;
clips longer than 15s still get a full observation PE, then a clamped replay envelope.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from omni_rewriter.adapters import H3Client  # noqa: E402
from omni_rewriter.config import Settings  # noqa: E402
from omni_rewriter.models import BaseRewrite, RewriteRequest  # noqa: E402
from omni_rewriter.reconstruct.evidence import EvidencePackConfig  # noqa: E402
from omni_rewriter.reconstruct.replay import envelope_for_h3_replay  # noqa: E402
from omni_rewriter.reconstruct.service import (  # noqa: E402
    ReconstructResult,
    reconstruct,
    result_payload,
)

DEMO_ROOT = ROOT / "outputs" / "reconstruct-demo"

CASES: list[dict[str, object]] = [
    {
        "id": "h3_t2va_10s",
        "title": "MiniMax-H3 official T2VA (~10s)",
        "source": "sources/h3_t2va_10s.mp4",
        "step_seconds": "0.6",
        "max_keyframes": 16,
        "origin": "https://github.com/MiniMax-AI/MiniMax-H3",
    },
    {
        "id": "h3_cinematic_15s",
        "title": "MiniMax-H3 cinematic showcase (~15s)",
        "source": "sources/h3_cinematic_15s.mp4",
        "step_seconds": "0.9",
        "max_keyframes": 16,
        "origin": "https://github.com/MiniMax-AI/MiniMax-H3",
    },
    {
        "id": "seedance_ornithopter_20s",
        "title": "Seedance 2.5 ornithopter promo (~20s, H3 replay 15s)",
        "source": "sources/seedance_ornithopter_20s.mp4",
        "step_seconds": "1.2",
        "max_keyframes": 16,
        "origin": "Seedance 2.5 public first-screen promo",
    },
    {
        "id": "h3_montage_40s",
        "title": "H3 official montage (~40s observe, H3 replay 15s)",
        "source": "sources/h3_montage_40s.mp4",
        "step_seconds": "2.5",
        "max_keyframes": 16,
        "origin": "https://github.com/MiniMax-AI/MiniMax-H3",
    },
]


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


async def _reconstruct_case(case: dict[str, object], demo_root: Path) -> Path:
    source = demo_root / str(case["source"])
    if not source.is_file() or source.stat().st_size == 0:
        raise FileNotFoundError(f"missing source clip: {source}")
    pack_dir = demo_root / "packs" / str(case["id"])
    pe_path = demo_root / "pe" / f"{case['id']}.json"
    print(f"reconstruct {case['id']} <- {source}", flush=True)
    result = await reconstruct(
        source=source,
        pack_dir=pack_dir,
        pack_config=EvidencePackConfig(
            max_duration_seconds="45",
            max_keyframes=int(case["max_keyframes"]),
            step_seconds=str(case["step_seconds"]),
        ),
    )
    if not isinstance(result, ReconstructResult):
        raise TypeError(f"expected ReconstructResult, got {type(result).__name__}")
    payload = result_payload(result)
    payload["demo"] = {
        "id": case["id"],
        "title": case["title"],
        "origin": case["origin"],
    }
    _write_json(pe_path, payload)
    replay = envelope_for_h3_replay(payload)
    replay["demo"] = payload["demo"]
    _write_json(demo_root / "pe" / f"{case['id']}.h3.json", replay)
    print(
        f"  wrote {pe_path} duration={payload['request']['duration_seconds']}s "
        f"replay={replay['h3_replay_window_seconds']}s",
        flush=True,
    )
    return pe_path


async def _generate_case(case: dict[str, object], demo_root: Path) -> Path:
    envelope_path = demo_root / "pe" / f"{case['id']}.h3.json"
    dest = demo_root / "replay" / f"{case['id']}.mp4"
    payload = json.loads(envelope_path.read_text(encoding="utf-8"))
    raw_request = dict(payload["request"])
    raw_request.pop("resolved_task", None)
    request = RewriteRequest.model_validate(raw_request)
    pe_text = BaseRewrite.model_validate(payload["output"]).render()
    settings = Settings.from_env()
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"generate {case['id']} -> {settings.h3_base_url}", flush=True)
    async with H3Client(settings.h3_client_config()) as client:
        task_id = await client.submit(request, pe_text)
        print(f"  task_id {task_id}", flush=True)
        result = await client.wait(task_id)
        await client.download(task_id, dest, result=result)
    meta = dest.with_suffix(".task.json")
    _write_json(
        meta,
        {
            "task_id": task_id,
            "out": str(dest),
            "window_seconds": payload["h3_replay_window_seconds"],
        },
    )
    print(f"  downloaded {dest} ({dest.stat().st_size} bytes)", flush=True)
    return dest


async def _run(args: argparse.Namespace) -> int:
    demo_root = args.demo_root
    selected = [case for case in CASES if args.only is None or case["id"] == args.only]
    if args.only and not selected:
        print(f"unknown case id: {args.only}", file=sys.stderr)
        return 1
    if not args.skip_reconstruct:
        for case in selected:
            await _reconstruct_case(case, demo_root)
    if args.generate:
        for case in selected:
            await _generate_case(case, demo_root)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo-root", type=Path, default=DEMO_ROOT)
    parser.add_argument("--only", type=str, default=None, help="Run a single case id")
    parser.add_argument(
        "--skip-reconstruct",
        action="store_true",
        help="Reuse existing pe/*.json and only generate",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Submit clamped PE to OMNI_WRITER_H3_BASE_URL (expand ≠ generate)",
    )
    args = parser.parse_args()
    os.environ.setdefault("OMNI_WRITER_TIMEOUT", "600")
    os.environ.setdefault("OMNI_WRITER_MAX_TOKENS", "4096")
    os.environ.setdefault("OMNI_WRITER_H3_BASE_URL", "http://127.0.0.1:30010")
    raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
