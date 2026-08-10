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
    """Dark endcard — bake text to PNG then hold; no live drawtext/zoom filters."""
    from PIL import Image, ImageDraw, ImageFont

    png = dest.with_suffix(".png")
    img = Image.new("RGB", (1344, 768), (28, 24, 34))
    dr = ImageDraw.Draw(img)
    try:
        title = ImageFont.truetype(FONT, 58)
        link = ImageFont.truetype(FONT, 28)
    except OSError:
        title = ImageFont.load_default()
        link = title
    dr.text((672, 360), "Omni-Rewriter", font=title, fill=(255, 255, 255), anchor="mm")
    dr.text(
        (672, 430),
        "github.com/WayneJin0918/Omni-Rewriter",
        font=link,
        fill=(184, 240, 216),
        anchor="mm",
    )
    img.save(png)
    run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-framerate",
            "24",
            "-i",
            str(png),
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-map",
            "0:v",
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


def _extract_last_frame(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Prefer sseof — end seeks with -ss are flaky on short re-encoded clips.
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-sseof",
            "-0.08",
            "-i",
            str(src),
            "-update",
            "1",
            "-frames:v",
            "1",
            str(dest),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if not dest.is_file() or dest.stat().st_size < 32:
        at = max(0.0, dur(src) * 0.92)
        subprocess.check_call(
            [
                "ffmpeg",
                "-y",
                "-ss",
                f"{at:.3f}",
                "-i",
                str(src),
                "-update",
                "1",
                "-frames:v",
                "1",
                str(dest),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    if not dest.is_file() or dest.stat().st_size < 32:
        raise RuntimeError(f"failed to extract hold frame from {src}")


def render_designed_hold_plate(freeze: Path, out_png: Path, *, kind: str) -> None:
    """Designed breath-hold from an existing frame (not a raw freeze clone)."""
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    w, h = 1344, 768
    base = Image.open(freeze).convert("RGB").resize((w, h), Image.Resampling.LANCZOS)
    soft = base.filter(ImageFilter.GaussianBlur(radius=3.4 if kind != "end" else 1.2))
    warm = Image.new("RGB", (w, h), (42, 28, 26))
    soft = Image.blend(soft, warm, 0.22 if kind.startswith("proof") else 0.28)

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(overlay)
    for i in range(0, 200, 4):
        a = int(110 * (1 - i / 200))
        dr.rectangle((0, 0, w, i), fill=(12, 10, 14, a))
        dr.rectangle((0, h - i, w, h), fill=(12, 10, 14, a))

    # Soft center wash + thin accent rule — keeps continuity without new copy.
    wash = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    wdr = ImageDraw.Draw(wash)
    wdr.ellipse((w // 2 - 420, h // 2 - 260, w // 2 + 420, h // 2 + 260), fill=(18, 12, 16, 70))
    wash = wash.filter(ImageFilter.GaussianBlur(radius=28))
    dr.rounded_rectangle(
        (w // 2 - 40, h // 2 - 8, w // 2 + 40, h // 2 - 5),
        radius=2,
        fill=(255, 210, 190, 150),
    )

    accent = {
        "intro": (184, 240, 216, 200),
        "proof": (255, 196, 176, 200),
        "models": (255, 220, 200, 190),
    }.get(kind.split("_")[0], (230, 220, 210, 180))
    dr.rounded_rectangle((48, h - 28, 52 + 120, h - 24), radius=2, fill=accent)

    try:
        font = ImageFont.truetype(FONT, 18)
    except OSError:
        font = ImageFont.load_default()
    label = {
        "intro": "PE",
        "proof": "RAW  |  PE",
        "models": "models",
    }.get(kind.split("_")[0], "")
    if label:
        dr.text((56, h - 52), label, font=font, fill=(245, 240, 235, 200), anchor="lt")

    composed = Image.alpha_composite(soft.convert("RGBA"), wash)
    composed = Image.alpha_composite(composed, overlay)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    composed.convert("RGB").save(out_png)


def _hold_clip_from_png(png: Path, dest: Path, seconds: float) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-framerate",
            "24",
            "-i",
            str(png),
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-filter_complex",
            (
                f"[0:v]scale=1344:768:flags=lanczos,format=yuv420p,"
                f"fade=t=in:st=0:d={min(0.28, seconds / 3):.2f}[v]"
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


def pad_tail_for_xfade(src: Path, dest: Path, pad: float, *, kind: str = "clip") -> None:
    """Append a designed hold (from last frame) + silence so acrossfade keeps dialogue intact."""
    if pad <= 0.01:
        run(["ffmpeg", "-y", "-i", str(src), "-c", "copy", str(dest)])
        return
    work = dest.parent / f"_hold_{dest.stem}"
    work.mkdir(parents=True, exist_ok=True)
    freeze = work / "tail.png"
    plate = work / "hold.png"
    hold = work / "hold.mp4"
    _extract_last_frame(src, freeze)
    render_designed_hold_plate(freeze, plate, kind=kind)
    _hold_clip_from_png(plate, hold, pad)
    # Soften the cut into silence: intro gets a longer settle; others a light ease-out.
    src_d = dur(src)
    fade = 0.95 if kind == "intro" else min(0.45, max(0.2, pad * 0.45))
    fade = min(fade, max(0.12, src_d - 0.05))
    fade_st = max(0.0, src_d - fade)
    # Concat original + designed hold (re-encode for matching timebase).
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-i",
            str(hold),
            "-filter_complex",
            (
                "[0:v]fps=24,format=yuv420p,setpts=PTS-STARTPTS[v0];"
                "[1:v]fps=24,format=yuv420p,setpts=PTS-STARTPTS[v1];"
                "[0:a]aformat=sample_rates=48000:channel_layouts=stereo,"
                f"afade=t=out:st={fade_st:.3f}:d={fade:.3f},"
                "asetpts=PTS-STARTPTS[a0];"
                "[1:a]aformat=sample_rates=48000:channel_layouts=stereo,asetpts=PTS-STARTPTS[a1];"
                "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]"
            ),
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


def _pad_kind(path: Path) -> str:
    name = path.name.lower()
    if "intro" in name:
        return "intro"
    if "proof" in name:
        return "proof"
    if "model" in name or "finale" in name:
        return "models"
    return "clip"


def xfade_concat(clips: list[Path], xfade_ds: list[float], dest: Path) -> None:
    """Soft video xfade; each outgoing tail is a designed hold regenerated from last frame."""
    assert len(clips) >= 2
    assert len(xfade_ds) == len(clips) - 1
    pad_dir = dest.parent / f"_xfade_pad_{dest.stem}"
    pad_dir.mkdir(parents=True, exist_ok=True)
    padded: list[Path] = []
    for i, clip in enumerate(clips):
        if i < len(xfade_ds):
            out = pad_dir / f"p{i:02d}.mp4"
            pad_tail_for_xfade(clip, out, xfade_ds[i], kind=_pad_kind(clip))
            padded.append(out)
        else:
            padded.append(clip)

    durs = [dur(p) for p in padded]
    offsets: list[tuple[float, float]] = []
    timeline = durs[0]
    for i, xd in enumerate(xfade_ds):
        # Fade lives inside the padded silence/freeze tail.
        offsets.append((xd, max(0.05, timeline - xd)))
        timeline = timeline + durs[i + 1] - xd

    inputs: list[str] = []
    for p in padded:
        inputs += ["-i", str(p)]
    parts: list[str] = []
    prev = "[0:v]"
    for i in range(1, len(padded)):
        xd, off = offsets[i - 1]
        out_l = f"[v{i}]" if i < len(padded) - 1 else "[vout]"
        parts.append(
            f"{prev}[{i}:v]xfade=transition=fade:duration={xd:.2f}:offset={off:.3f}{out_l}"
        )
        prev = out_l
    # Audio crossfade shorter than video so next-clip dialogue is not ducked as hard.
    # Intro→proof uses a longer settle so the opening bed does not hard-stop.
    prev_a = "[0:a]"
    for i in range(1, len(padded)):
        xd, _ = offsets[i - 1]
        if i == 1 and _pad_kind(clips[0]) == "intro":
            ad = min(xd, 0.85)
        else:
            ad = min(xd, 0.22)
        out_l = f"[a{i}]" if i < len(padded) - 1 else "[aout]"
        parts.append(f"{prev_a}[{i}:a]acrossfade=d={ad:.2f}:c1=tri:c2=tri{out_l}")
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
    parser.add_argument(
        "--end",
        type=Path,
        default=None,
        help="Optional prebuilt endcard (e.g. with outro VO). Default: generate static card.",
    )
    parser.add_argument(
        "--no-endcard",
        action="store_true",
        help="Skip endcard — use when --models-finale already includes the CTA hold",
    )
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
    proof_to_models = 0.5

    if args.models_finale is not None:
        finale_n = work / "n_models_finale.mp4"
        normalize(args.models_finale, finale_n, "eq=saturation=1.04:contrast=1.02")
        model_clips = [finale_n]
        models_mode = "designed_finale"
        model_xfade = []
        proof_to_models = 1.0
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

    end_clips: list[Path] = []
    end_xfade: list[float] = []
    if not args.no_endcard:
        end = work / "n_end.mp4"
        if args.end is not None:
            normalize(args.end, end)
        else:
            make_endcard(end, seconds=2.2)
        end_clips = [end]
        end_xfade = [0.25]

    # Soft module transitions; pads are designed holds so speech survives.
    # Intro→proof keeps ~1s of breath so the first proof does not slam in.
    clips = [intro_n, *proof_n, *model_clips, *end_clips]
    # intro→proof0, proof gaps, proof→models, optional models internal, models→end
    xfade = (
        [1.0]
        + [0.35] * max(len(proof_n) - 1, 0)
        + ([max(proof_to_models, 0.85)] if model_clips else [])
        + model_xfade
        + end_xfade
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
