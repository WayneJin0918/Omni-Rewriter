#!/usr/bin/env python3
"""Submit a validated promo PE envelope JSON to a local/remote H3 adapter."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from omni_rewriter.adapters import H3Client  # noqa: E402
from omni_rewriter.config import Settings  # noqa: E402
from omni_rewriter.models import BaseRewrite, RewriteRequest  # noqa: E402


async def _run(envelope: Path, dest: Path) -> str:
    payload = json.loads(envelope.read_text())
    request = RewriteRequest.model_validate(payload["request"])
    pe_text = BaseRewrite.model_validate(payload["output"]).render()
    settings = Settings.from_env()
    dest.parent.mkdir(parents=True, exist_ok=True)
    async with H3Client(settings.h3_client_config()) as client:
        print(f"submit {request.resolved_task.value} -> {settings.h3_base_url}", flush=True)
        task_id = await client.submit(request, pe_text)
        print(f"task_id {task_id}", flush=True)
        result = await client.wait(task_id)
        await client.download(task_id, dest, result=result)
        print(f"downloaded {dest} ({dest.stat().st_size} bytes)", flush=True)
        return task_id


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("envelope", type=Path, help="JSON with request + output (BaseRewrite)")
    parser.add_argument("--out", type=Path, required=True, help="Destination mp4 path")
    args = parser.parse_args()
    task_id = asyncio.run(_run(args.envelope, args.out))
    meta = args.out.with_suffix(".task.json")
    meta.write_text(json.dumps({"task_id": task_id, "out": str(args.out)}, indent=2) + "\n")


if __name__ == "__main__":
    main()
