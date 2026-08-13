#!/usr/bin/env python3
"""Build labeled Source | Omni-Rewriter compare videos, GIFs, and a 10s reel.

Each case uses the first 10s of source and replay. Audio comes from the replay
arm. English labels use a Latin font so CJK-only fallbacks cannot tofu. Do not
commit full mp4.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/comfortaa/Comfortaa-Bold.ttf",
    "/usr/share/fonts/truetype/lato/Lato-Bold.ttf",
)
LEFT_LABEL = "Source"
RIGHT_LABEL = "Omni-Rewriter"
ROOT = Path(__file__).resolve().parents[2]
DEMO_ROOT = ROOT / "outputs" / "reconstruct-demo"
GALLERY = ROOT / "docs" / "assets" / "gallery" / "reconstruct"
COMPARE_WINDOW = 10.0

CASES = [
    {
        "id": "h3_t2va_10s",
        "title": "MiniMax-H3 official T2VA",
        "caption": "First 10s Source vs Omni-Rewriter",
        "source": "sources/h3_t2va_10s.mp4",
        "replay": "replay/h3_t2va_10s.mp4",
        "gif_start": 2.0,
    },
    {
        "id": "h3_cinematic_15s",
        "title": "MiniMax-H3 cinematic showcase",
        "caption": "First 10s Source vs Omni-Rewriter",
        "source": "sources/h3_cinematic_15s.mp4",
        "replay": "replay/h3_cinematic_15s.mp4",
        "gif_start": 3.0,
    },
    {
        "id": "seedance_ornithopter_20s",
        "title": "Seedance 2.5 ornithopter",
        "caption": "First 10s Source vs Omni-Rewriter (public H3 generate window is 4–15s)",
        "source": "sources/seedance_ornithopter_20s.mp4",
        "replay": "replay/seedance_ornithopter_20s.mp4",
        "gif_start": 2.0,
    },
    {
        "id": "h3_montage_40s",
        "title": "H3 official montage",
        "caption": "First 10s Source vs Omni-Rewriter (public H3 generate window is 4–15s)",
        "source": "sources/h3_montage_40s.mp4",
        "replay": "replay/h3_montage_40s.mp4",
        "gif_start": 2.0,
    },
]


def run(cmd: list[str]) -> None:
    subprocess.check_call(cmd)


def latin_font() -> str:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).is_file():
            return candidate.replace("\\", "/").replace(":", "\\:")
    raise FileNotFoundError("no Latin TTF found among FONT_CANDIDATES")


def probe_duration(path: Path) -> float:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(completed.stdout.strip())


def compare_duration(source: Path, replay: Path) -> float:
    """Align both arms to the first 10s (and the shorter clip)."""

    return min(COMPARE_WINDOW, probe_duration(source), probe_duration(replay))


def trim_source(source: Path, dest: Path, duration: float) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-t",
            f"{duration:.3f}",
            "-vf",
            "scale=-2:768,setsar=1",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            str(dest),
        ]
    )


def build_labeled_compare(
    raw: Path,
    replay: Path,
    dest: Path,
    *,
    duration: float,
) -> None:
    """Left/right card with burned-in Source vs Omni-Rewriter."""

    font = latin_font()
    filt = (
        f"[0:v]trim=start=0:duration={duration},setpts=PTS-STARTPTS,"
        f"scale=640:360:force_original_aspect_ratio=decrease,"
        f"pad=640:420:(ow-iw)/2:52:0x1C1822,setsar=1,"
        f"drawbox=x=0:y=0:w=640:h=48:color=0xFFB4A8@0.95:t=fill,"
        f"drawtext=fontfile={font}:text='{LEFT_LABEL}':x=(w-text_w)/2:y=12:"
        f"fontsize=22:fontcolor=0x1C1822[v0];"
        f"[1:v]trim=start=0:duration={duration},setpts=PTS-STARTPTS,"
        f"scale=640:360:force_original_aspect_ratio=decrease,"
        f"pad=640:420:(ow-iw)/2:52:0x1C1822,setsar=1,"
        f"drawbox=x=0:y=0:w=640:h=48:color=0xB8F0D8@0.95:t=fill,"
        f"drawtext=fontfile={font}:text='{RIGHT_LABEL}':x=(w-text_w)/2:y=12:"
        f"fontsize=22:fontcolor=0x1C1822[v1];"
        f"[1:a]atrim=start=0:duration={duration},asetpts=PTS-STARTPTS,"
        f"aformat=sample_rates=48000:channel_layouts=stereo[a];"
        f"[v0][v1]hstack=inputs=2,format=yuv420p,fps=24[vout]"
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(raw),
            "-i",
            str(replay),
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


def concat_reel(clips: list[Path], dest: Path) -> None:
    """Hard-concat labeled 10s cards into one reel. Audio stays on the replay arm."""

    if not clips:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    if len(clips) == 1:
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(clips[0]),
                "-c",
                "copy",
                str(dest),
            ]
        )
        return
    cmd: list[str] = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for clip in clips:
        cmd.extend(["-i", str(clip)])
    parts: list[str] = []
    concat_in = ""
    for index in range(len(clips)):
        parts.append(
            f"[{index}:v]fps=24,format=yuv420p,settb=AVTB,setpts=PTS-STARTPTS[v{index}];"
            f"[{index}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
            f"asetpts=PTS-STARTPTS[a{index}]"
        )
        concat_in += f"[v{index}][a{index}]"
    filt = ";".join(parts) + f";{concat_in}concat=n={len(clips)}:v=1:a=1[v][a]"
    cmd.extend(
        [
            "-filter_complex",
            filt,
            "-map",
            "[v]",
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
            "-movflags",
            "+faststart",
            str(dest),
        ]
    )
    run(cmd)


def build_gif(source: Path, dest: Path, *, start: float, duration: float = 3.5) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            str(start),
            "-t",
            str(duration),
            "-i",
            str(source),
            "-filter_complex",
            "[0:v]fps=6,scale=640:-2:flags=lanczos,split[frames][palette_input];"
            "[palette_input]palettegen=max_colors=96:stats_mode=diff[palette];"
            "[frames][palette]paletteuse=dither=sierra2_4a:diff_mode=rectangle",
            "-an",
            "-loop",
            "0",
            str(dest),
        ]
    )


def write_index(cases: list[dict[str, object]]) -> None:
    sections = []
    for case in cases:
        cid = case["id"]
        sections.append(
            f"""    <section class="scene">
      <h2>{case["title"]}</h2>
      <p class="note">{case["caption"]}. Expand ≠ generate. Left is Source; right is Omni-Rewriter PE replayed on MiniMax-H3.</p>
      <figure>
        <img src="{cid}_compare.gif" alt="{case["title"]} Source vs Omni-Rewriter">
      </figure>
    </section>"""
        )
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Omni-Rewriter Source vs Omni-Rewriter</title>
  <style>
    :root {{ color-scheme: light dark; font-family: ui-sans-serif, system-ui, sans-serif; }}
    body {{ max-width: 920px; margin: 0 auto; padding: 2rem 1rem; }}
    h1 {{ margin-bottom: 0.4rem; }}
    .note {{ color: #666; font-size: 0.92rem; }}
    .scene {{ margin: 2rem 0; }}
    figure {{ margin: 0; }}
    img {{ display: block; width: 100%; height: auto; border-radius: 0.4rem; background: #111; }}
  </style>
</head>
<body>
  <main>
    <h1>Source vs Omni-Rewriter</h1>
    <p>Left: Source (first 10s). Right: Omni-Rewriter PE replayed on MiniMax-H3.
    Expand ≠ generate. Public H3 generate window is integer 4–15s.</p>
{chr(10).join(sections)}
  </main>
</body>
</html>
"""
    GALLERY.mkdir(parents=True, exist_ok=True)
    (GALLERY / "index.html").write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo-root", type=Path, default=DEMO_ROOT)
    args = parser.parse_args()
    ready: list[dict[str, object]] = []
    compares: list[Path] = []
    for case in CASES:
        source = args.demo_root / str(case["source"])
        replay = args.demo_root / str(case["replay"])
        if not source.is_file() or not replay.is_file():
            missing = source.name if not source.is_file() else replay.name
            print(f"skip {case['id']}: missing {missing}")
            continue
        duration = compare_duration(source, replay)
        trimmed = args.demo_root / "sources" / "compare10" / f"{case['id']}.mp4"
        trim_source(source, trimmed, duration)
        compare = args.demo_root / "compare" / f"{case['id']}_source_vs_h3_omni_replay.mp4"
        build_labeled_compare(trimmed, replay, compare, duration=duration)
        print(f"wrote {compare} ({duration:.3f}s)")
        gif = GALLERY / f"{case['id']}_compare.gif"
        build_gif(compare, gif, start=float(case["gif_start"]))
        ready.append(case)
        compares.append(compare)
    reel = args.demo_root / "compare" / "source_vs_omni_rewriter_10s_reel.mp4"
    concat_reel(compares, reel)
    if compares:
        print(f"wrote {reel} ({len(compares) * COMPARE_WINDOW:.0f}s target)")
    write_index(ready or CASES)
    manifest = [
        {
            "id": case["id"],
            "title": case["title"],
            "caption": case["caption"],
            "compare_gif": f"{case['id']}_compare.gif",
        }
        for case in ready
    ]
    (GALLERY / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"gallery index {GALLERY / 'index.html'}")


if __name__ == "__main__":
    main()
