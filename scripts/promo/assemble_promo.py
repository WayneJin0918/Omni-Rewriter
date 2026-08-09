#!/usr/bin/env python3
"""Assemble Omni-Rewriter promo: intro → proof → models bridge/brand → endcard."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

FONT = "/usr/share/fonts/truetype/comfortaa/Comfortaa-Bold.ttf"


def run(cmd: list[str]) -> None:
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def dur(path: Path) -> float:
    return float(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nw=1:nk=1",
                str(path),
            ]
        )
        .decode()
        .strip()
    )


def has_audio(path: Path) -> bool:
    return bool(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a",
                "-show_entries",
                "stream=codec_type",
                "-of",
                "csv=p=0",
                str(path),
            ]
        )
        .decode()
        .strip()
    )


def normalize(src: Path, dest: Path, vf: str | None = None) -> None:
    if has_audio(src):
        cmd = ["ffmpeg", "-y", "-i", str(src)]
        if vf:
            cmd += ["-vf", vf]
        cmd += [
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "24",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(dest),
        ]
        run(cmd)
    else:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-shortest",
        ]
        if vf:
            cmd += ["-vf", vf]
        cmd += [
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "24",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(dest),
        ]
        run(cmd)


def make_endcard(dest: Path, seconds: float = 3.5) -> None:
    """Dark endcard with gentle push-in."""
    frames = max(int(seconds * 24), 24)
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=0x1C1822:s=1500x858:d={seconds}",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-filter_complex",
            (
                f"[0:v]drawtext=fontfile={FONT}:text='Omni-Rewriter':"
                "x=(w-text_w)/2:y=(h/2)-56:fontsize=58:fontcolor=white,"
                f"drawtext=fontfile={FONT}:text='github.com/WayneJin0918/Omni-Rewriter':"
                "x=(w-text_w)/2:y=(h/2)+18:fontsize=28:fontcolor=0xB8F0D8,"
                f"zoompan=z='min(1.06,1+0.0012*on)':x='iw/2-(iw/zoom/2)':"
                f"y='ih/2-(ih/zoom/2)':d={frames}:s=1344x768:fps=24,"
                f"fade=t=in:st=0:d=0.45,format=yuv420p[v]"
            ),
            "-map",
            "[v]",
            "-map",
            "1:a",
            "-t",
            str(seconds),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-shortest",
            str(dest),
        ]
    )


def overlay_plates_on_broll(
    broll: Path,
    plate: Path,
    dest: Path,
    *,
    start_ratio: float = 0.28,
    fade_in: float = 1.1,
) -> None:
    """One soft name-chip burn-in over H3 B-roll (scene stays visible underneath)."""
    b_dur = dur(broll)
    start = max(0.0, b_dur * start_ratio)
    # alpha fade-in so names appear once, gently
    filt = (
        f"[1:v]fps=24,scale={1344}:{768},format=rgba,"
        f"fade=t=in:st={start:.3f}:d={fade_in:.2f}:alpha=1[p];"
        f"[0:v][p]overlay=0:0:format=auto[vout]"
    )
    plate_args: list[str]
    if plate.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
        plate_args = ["-loop", "1", "-i", str(plate)]
    else:
        plate_args = ["-i", str(plate)]
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(broll),
            *plate_args,
            "-filter_complex",
            filt,
            "-map",
            "[vout]",
            "-map",
            "0:a?",
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
            str(b_dur),
            str(dest),
        ]
    )


def xfade_concat(clips: list[Path], xfade_ds: list[float], dest: Path) -> None:
    assert len(clips) >= 2
    assert len(xfade_ds) == len(clips) - 1
    durs = [dur(p) for p in clips]
    offsets: list[tuple[float, float]] = []
    timeline = durs[0]
    for i, xd in enumerate(xfade_ds):
        offsets.append((xd, timeline - xd))
        timeline = timeline + durs[i + 1] - xd

    inputs: list[str] = []
    for p in clips:
        inputs += ["-i", str(p)]
    parts: list[str] = []
    prev = "[0:v]"
    for i in range(1, len(clips)):
        xd, off = offsets[i - 1]
        out_l = f"[v{i}]" if i < len(clips) - 1 else "[vout]"
        parts.append(
            f"{prev}[{i}:v]xfade=transition=fade:duration={xd:.2f}:offset={off:.3f}{out_l}"
        )
        prev = out_l
    prev_a = "[0:a]"
    for i in range(1, len(clips)):
        xd, _ = offsets[i - 1]
        out_l = f"[a{i}]" if i < len(clips) - 1 else "[aout]"
        parts.append(f"{prev_a}[{i}:a]acrossfade=d={xd:.2f}{out_l}")
        prev_a = out_l

    run(
        [
            "ffmpeg",
            "-y",
            *inputs,
            "-filter_complex",
            ";".join(parts),
            "-map",
            "[vout]",
            "-map",
            "[aout]",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            str(dest),
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intro", type=Path, required=True)
    parser.add_argument("--proof", type=Path, nargs="+", required=True)
    parser.add_argument(
        "--models-finale",
        type=Path,
        default=None,
        help="Preferred designed finale (bridge→brand→lanes) from build_models_finale.py",
    )
    parser.add_argument(
        "--models-broll",
        type=Path,
        default=None,
        help="Legacy live H3 hanging-board B-roll (omit for designed finale)",
    )
    parser.add_argument(
        "--models-bridge",
        type=Path,
        default=None,
        help="Legacy: atmosphere bridge before brand hold",
    )
    parser.add_argument(
        "--models-brand-hold",
        type=Path,
        default=None,
        help="Preferred: centered Omni-Rewriter brand fade (+ optional model list)",
    )
    parser.add_argument(
        "--models-named-hold",
        type=Path,
        default=None,
        help="Legacy: freeze with names burned onto hanging slats",
    )
    parser.add_argument(
        "--models-broll-seconds",
        type=float,
        default=3.2,
        help="Seconds of live H3 models B-roll before brand/named hold (legacy)",
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    args = parser.parse_args()

    work = args.work_dir
    work.mkdir(parents=True, exist_ok=True)

    intro_n = work / "n_intro.mp4"
    normalize(args.intro, intro_n, "eq=saturation=1.06:contrast=1.02")

    proof_n = []
    for i, p in enumerate(args.proof):
        dest = work / f"n_proof_{i}.mp4"
        normalize(p, dest)
        proof_n.append(dest)

    # Models act (preferred): single designed finale. Legacy: bridge+brand / broll paths.
    model_clips: list[Path] = []
    model_xfade: list[float] = []
    hold_src = args.models_brand_hold or args.models_named_hold
    proof_to_models = 0.9

    if args.models_finale is not None:
        finale_n = work / "n_models_finale.mp4"
        normalize(args.models_finale, finale_n, "eq=saturation=1.04:contrast=1.02")
        model_clips = [finale_n]
        models_mode = "designed_finale"
        model_xfade = []
    elif args.models_bridge is not None and args.models_brand_hold is not None:
        bridge_n = work / "n_models_bridge.mp4"
        hold_n = work / "n_models_hold.mp4"
        normalize(args.models_bridge, bridge_n, "eq=saturation=1.04:contrast=1.02")
        normalize(args.models_brand_hold, hold_n)
        model_clips = [bridge_n, hold_n]
        models_mode = "bridge_then_brand"
        model_xfade = [0.65]
        proof_to_models = 0.7
    elif hold_src is not None:
        if args.models_broll is None:
            raise SystemExit(
                "legacy brand/named hold requires --models-broll, or use --models-finale"
            )
        head = work / "n_broll_head.mp4"
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(args.models_broll),
                "-t",
                str(args.models_broll_seconds),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-r",
                "24",
                "-c:a",
                "aac",
                "-b:a",
                "160k",
                "-ar",
                "48000",
                "-ac",
                "2",
                str(head),
            ]
        )
        named_n = work / "n_models_hold.mp4"
        normalize(hold_src, named_n)
        model_clips = [head, named_n]
        models_mode = (
            "broll_then_brand_title"
            if args.models_brand_hold is not None
            else "broll_then_slat_names"
        )
        model_xfade = [0.7]
        proof_to_models = 0.55
    else:
        if args.models_broll is None:
            raise SystemExit(
                "provide --models-finale, or --models-bridge + brand, or --models-broll"
            )
        broll_n = work / "n_broll.mp4"
        normalize(args.models_broll, broll_n, "eq=saturation=1.05:contrast=1.02")
        model_clips = [broll_n]
        models_mode = "broll_only"
        model_xfade = []
        proof_to_models = 0.55

    end = work / "n_end.mp4"
    make_endcard(end, seconds=2.8)

    # Soft module transitions; longer intro→proof to hide hard cut
    clips = [intro_n, *proof_n, *model_clips, end]
    # intro→proof0, proof gaps, proof→models, optional models internal, models→end
    xfade = (
        [1.0]
        + [0.45] * max(len(proof_n) - 1, 0)
        + ([proof_to_models] if model_clips else [])
        + model_xfade
        + [0.6]
    )
    assert len(xfade) == len(clips) - 1, (len(xfade), len(clips), clips)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    xfade_concat(clips, xfade, args.out)
    meta = {
        "out": str(args.out),
        "duration": dur(args.out),
        "bytes": args.out.stat().st_size,
        "clips": [str(c) for c in clips],
        "models_mode": models_mode,
    }
    args.out.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
