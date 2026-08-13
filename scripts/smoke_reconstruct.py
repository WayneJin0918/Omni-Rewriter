#!/usr/bin/env python3
"""Local reconstruct smoke: pack → validate observation → optional live Writer.

Does not generate media. Does not commit mp4. Expand ≠ generate.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from omni_rewriter.models.observation import VideoObservation  # noqa: E402
from omni_rewriter.service import validate_output  # noqa: E402

KITE = ROOT / "docs/design/examples/observation_kite.json"


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    print("+", " ".join(args), flush=True)
    completed = subprocess.run(args, cwd=ROOT, env=env, text=True, check=False, capture_output=True)
    if completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
    if completed.stderr:
        print(completed.stderr, end="" if completed.stderr.endswith("\n") else "\n")
    return completed


def _synthesize(path: Path, seconds: int = 6) -> None:
    cmd = [
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
    ]
    completed = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise SystemExit(f"ffmpeg synthesize failed: {completed.stderr[-400:]}")


def _writer_up() -> bool:
    import socket

    parsed = os.environ.get("OMNI_WRITER_BACKEND_BASE_URL", "http://127.0.0.1:8000/v1")
    host = "127.0.0.1"
    port = 8000
    if "://" in parsed:
        rest = parsed.split("://", 1)[1]
        hostport = rest.split("/", 1)[0]
        if ":" in hostport:
            host, port_s = hostport.rsplit(":", 1)
            port = int(port_s)
        else:
            host = hostport
    sock = socket.socket()
    sock.settimeout(0.4)
    try:
        return sock.connect_ex((host, port)) == 0
    finally:
        sock.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--clip",
        type=Path,
        help="Existing local mp4 (observe ≤45s). Default: synthesize a 6s lavfi clip.",
    )
    parser.add_argument(
        "--pack-dir",
        type=Path,
        default=ROOT / "outputs" / "reconstruct-smoke",
    )
    args = parser.parse_args()
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        print("FAIL: ffmpeg/ffprobe not on PATH")
        return 1

    args.pack_dir.mkdir(parents=True, exist_ok=True)
    clip = args.clip
    if clip is None:
        clip = args.pack_dir / "smoke_src.mp4"
        _synthesize(clip)
        print(f"OK synthesize {clip}")
    elif not clip.is_file():
        print(f"FAIL: clip not found: {clip}")
        return 1

    pack = _run(
        [
            sys.executable,
            "-m",
            "omni_rewriter.cli",
            "reconstruct",
            str(clip),
            "--pack-only",
            "--pack-dir",
            str(args.pack_dir / "pack"),
        ]
    )
    if pack.returncode != 0:
        print(pack.stdout)
        print(pack.stderr)
        print("FAIL: pack-only")
        return pack.returncode
    summary = json.loads(pack.stdout)
    print(
        "OK pack-only",
        summary["probe"]["duration_seconds"],
        f"{len(summary['frames'])} frames",
        "audio" if summary.get("audio_wav") else "silent",
    )

    envelope = json.loads(KITE.read_text(encoding="utf-8"))
    VideoObservation.model_validate(envelope["observation"])
    validate_output(envelope)
    print("OK validate observation_kite envelope (no Writer)")

    if not _writer_up():
        print(
            "SKIP live reconstruct --from-observation (no Writer at OMNI_WRITER_BACKEND_BASE_URL)"
        )
        print("SMOKE reconstruct: pack + observation validate passed")
        return 0

    live = _run(
        [
            sys.executable,
            "-m",
            "omni_rewriter.cli",
            "reconstruct",
            "--from-observation",
            str(KITE),
        ]
    )
    if live.returncode != 0:
        print(live.stdout)
        print(live.stderr)
        print("FAIL: live --from-observation")
        return live.returncode
    payload = json.loads(live.stdout)
    out = args.pack_dir / "from_observation.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("OK live --from-observation", "repairs", payload.get("repairs"), "→", out)
    print("SMOKE reconstruct: pack + validate + live observation→PE passed")
    print("Generate remains a separate H3 adapter step.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
