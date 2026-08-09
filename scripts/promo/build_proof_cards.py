#!/usr/bin/env python3
"""Build refined RAW|PE proof cards with PE original audio."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

FONT = "/usr/share/fonts/truetype/comfortaa/Comfortaa-Bold.ttf"


def run(cmd: list[str]) -> None:
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def build_card(
    raw: Path,
    pe: Path,
    dest: Path,
    *,
    start: float,
    duration: float,
) -> None:
    """Side-by-side refined cards; audio from PE only."""
    filt = (
        f"[0:v]trim=start={start}:duration={duration},setpts=PTS-STARTPTS,"
        f"scale=560:320:force_original_aspect_ratio=decrease,"
        f"pad=620:400:30:50:0x2A2430,setsar=1,"
        f"drawbox=x=8:y=8:w=604:h=384:color=white@0.18:t=3,"
        f"drawbox=x=20:y=20:w=90:h=34:color=0xFFB4A8@0.92:t=fill,"
        f"drawtext=fontfile={FONT}:text='RAW':x=34:y=24:fontsize=22:fontcolor=0x1C1822[v0];"
        f"[1:v]trim=start={start}:duration={duration},setpts=PTS-STARTPTS,"
        f"scale=560:320:force_original_aspect_ratio=decrease,"
        f"pad=620:400:30:50:0x2A2430,setsar=1,"
        f"drawbox=x=8:y=8:w=604:h=384:color=white@0.18:t=3,"
        f"drawbox=x=20:y=20:w=70:h=34:color=0xB8F0D8@0.92:t=fill,"
        f"drawtext=fontfile={FONT}:text='PE':x=34:y=24:fontsize=22:fontcolor=0x1C1822[v1];"
        f"[1:a]atrim=start={start}:duration={duration},asetpts=PTS-STARTPTS,"
        f"aformat=sample_rates=48000:channel_layouts=stereo[a];"
        f"[v0][v1]hstack=inputs=2,pad=1344:768:(ow-iw)/2:(oh-ih)/2:0x1C1822,"
        f"eq=saturation=1.08:contrast=1.04,fps=24[vout]"
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(raw),
            "-i",
            str(pe),
            "-filter_complex",
            filt,
            "-map",
            "[vout]",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-t",
            str(duration),
            str(dest),
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="JSON list of {id, raw, pe, start, duration, out}",
    )
    args = parser.parse_args()
    items = json.loads(args.manifest.read_text())
    for item in items:
        dest = Path(item["out"])
        build_card(
            Path(item["raw"]),
            Path(item["pe"]),
            dest,
            start=float(item.get("start", 3.0)),
            duration=float(item.get("duration", 3.8)),
        )
        print(f"wrote {dest}")


if __name__ == "__main__":
    main()
