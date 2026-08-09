#!/usr/bin/env python3
"""Submit multiple H3 promo takes (different seeds) and download winners.

The local MiniMax-H3 service exposes one TI2V pipeline across 8 GPUs; jobs typically
queue. This still fans out submits so the 8-GPU node stays busy regenerating takes.
"""

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


async def _one(
    client: H3Client,
    envelope: Path,
    dest: Path,
    seed: int,
    *,
    duration: int | None,
) -> dict:
    payload = json.loads(envelope.read_text())
    request = RewriteRequest.model_validate(payload["request"])
    meta = dict(request.metadata)
    meta["seed"] = str(seed)
    request = request.model_copy(update={"metadata": meta})
    if duration is not None:
        request = request.model_copy(update={"duration_seconds": duration})
        out = dict(payload["output"])
        out["duration_seconds"] = str(duration)
        pe_text = BaseRewrite.model_validate(out).render()
    else:
        pe_text = BaseRewrite.model_validate(payload["output"]).render()

    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"submit seed={seed} -> {dest.name}", flush=True)
    task_id = await client.submit(request, pe_text)
    print(f"  task_id {task_id} seed={seed}", flush=True)
    # Long H3 jobs sometimes drop the poll connection; retry wait/query.
    result = None
    last_err: Exception | None = None
    for attempt in range(40):
        try:
            result = await client.wait(task_id)
            break
        except Exception as exc:  # noqa: BLE001 - transport flakes mid-wait
            last_err = exc
            print(f"  wait retry seed={seed} attempt={attempt} err={type(exc).__name__}", flush=True)
            await asyncio.sleep(8)
    if result is None:
        raise RuntimeError(f"wait failed for seed={seed} task={task_id}: {last_err}")
    await client.download(task_id, dest, result=result)
    info = {
        "seed": seed,
        "task_id": task_id,
        "out": str(dest),
        "bytes": dest.stat().st_size,
    }
    dest.with_suffix(".task.json").write_text(json.dumps(info, indent=2) + "\n")
    print(f"downloaded {dest} ({info['bytes']} bytes)", flush=True)
    return info


async def _run(
    envelope: Path,
    out_dir: Path,
    seeds: list[int],
    duration: int | None,
    *,
    prefix: str,
) -> list[dict]:
    settings = Settings.from_env()
    out_dir.mkdir(parents=True, exist_ok=True)
    async with H3Client(settings.h3_client_config()) as client:
        # Submit/wait concurrently so the queue fills; the 8-GPU node drains jobs.
        tasks = [
            _one(client, envelope, out_dir / f"{prefix}_seed{seed}.mp4", seed, duration=duration)
            for seed in seeds
        ]
        return list(await asyncio.gather(*tasks, return_exceptions=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("envelope", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument(
        "--prefix",
        type=str,
        default=None,
        help="Output filename prefix (default: envelope stem)",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[98210, 98211, 98212, 98213, 98214, 98215, 98216, 98217],
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=None,
        help="Optional H3 duration override (4-15). Default: envelope duration.",
    )
    args = parser.parse_args()
    prefix = args.prefix or args.envelope.stem
    results = asyncio.run(_run(args.envelope, args.out_dir, args.seeds, args.duration, prefix=prefix))
    manifest = args.out_dir / "batch_manifest.json"
    manifest.write_text(json.dumps({"takes": results}, indent=2) + "\n")
    print(json.dumps({"takes": results}, indent=2))


if __name__ == "__main__":
    main()
