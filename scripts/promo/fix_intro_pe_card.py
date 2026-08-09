#!/usr/bin/env python3
"""Replace garbled H3 PE close-up in intro with a clean designed PE hero card."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1344, 768
FONT = "/usr/share/fonts/truetype/comfortaa/Comfortaa-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/comfortaa/Comfortaa-Regular.ttf"


def _font(size: int, *, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (FONT if bold else FONT_REG, FONT, "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def extract_freeze(src: Path, at: float, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(at),
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


def render_clean_pe(freeze: Path, out_png: Path) -> None:
    """Readable PE hero — exact product strings only, no fake body copy."""
    base = Image.open(freeze).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    soft = base.filter(ImageFilter.GaussianBlur(radius=2.8))
    tint = Image.new("RGB", (W, H), (48, 32, 28))
    soft = Image.blend(soft, tint, 0.18)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(overlay)

    # frosted card
    card = (W // 2 - 250, H // 2 - 250, W // 2 + 250, H // 2 + 250)
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sdr = ImageDraw.Draw(shadow)
    sdr.rounded_rectangle(
        (card[0] + 10, card[1] + 14, card[2] + 10, card[3] + 14),
        radius=36,
        fill=(20, 12, 10, 70),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=12))
    dr.rounded_rectangle(card, radius=36, fill=(255, 252, 248, 210))
    # mint edge glow
    dr.rounded_rectangle(card, radius=36, outline=(184, 240, 216, 220), width=3)

    pe = _font(28)
    title = _font(44)
    body = _font(20, bold=False)
    small = _font(18, bold=False)
    cx = W // 2
    top = card[1] + 48

    dr.text((card[0] + 48, top), "PE", font=pe, fill=(56, 160, 130, 255), anchor="lt")
    dr.text((cx, top + 52), "Omni-Rewriter", font=title, fill=(28, 22, 24, 255), anchor="mm")

    # prompt field — exact messy prompt from intro
    field = (card[0] + 40, top + 100, card[2] - 40, top + 168)
    dr.rounded_rectangle(field, radius=16, fill=(245, 240, 235, 240))
    dr.text((cx, top + 118), "prompt", font=small, fill=(140, 120, 110, 220), anchor="mm")
    dr.text(
        (cx, top + 146),
        "make a cool video somehow",
        font=body,
        fill=(36, 28, 26, 255),
        anchor="mm",
    )

    stages = ["Analyze", "Draft", "Validate", "Repair", "Render"]
    colors = [
        (160, 220, 230, 235),
        (255, 190, 200, 235),
        (180, 230, 200, 235),
        (250, 220, 150, 235),
        (210, 195, 240, 235),
    ]
    chip_w, gap = 78, 8
    total = len(stages) * chip_w + (len(stages) - 1) * gap
    x0 = cx - total // 2
    y = top + 198
    for i, (name, col) in enumerate(zip(stages, colors)):
        x = x0 + i * (chip_w + gap)
        dr.rounded_rectangle((x, y, x + chip_w, y + 34), radius=10, fill=col)
        dr.text((x + chip_w // 2, y + 17), name, font=small, fill=(32, 26, 28, 245), anchor="mm")

    # footer
    foot = (card[0] + 70, top + 268, card[2] - 70, top + 318)
    dr.rounded_rectangle(foot, radius=18, fill=(184, 240, 216, 230))
    dr.text((cx, top + 293), "to production-ready", font=body, fill=(24, 48, 40, 255), anchor="mm")

    composed = Image.alpha_composite(soft.convert("RGBA"), shadow)
    composed = Image.alpha_composite(composed, overlay)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    composed.convert("RGB").save(out_png)


def still_hold(png: Path, audio_src: Path, dest: Path, *, seconds: float, audio_start: float) -> None:
    frames = max(int(seconds * 24), 24)
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(png),
            "-i",
            str(audio_src),
            "-filter_complex",
            (
                f"[0:v]scale=1480:846,zoompan=z='min(1.04,1+0.0012*on)':"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps=24,"
                f"format=yuv420p,fade=t=in:st=0:d=0.45[v];"
                f"[1:a]atrim=start={audio_start:.2f}:duration={seconds},asetpts=PTS-STARTPTS,"
                f"afade=t=in:st=0:d=0.35,aformat=sample_rates=48000:channel_layouts=stereo[a]"
            ),
            "-map",
            "[v]",
            "-map",
            "[a]",
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
            str(dest),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intro", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--keep-until",
        type=float,
        default=7.6,
        help="Seconds of original intro to keep before clean PE card",
    )
    parser.add_argument("--pe-seconds", type=float, default=3.4)
    parser.add_argument("--xfade", type=float, default=0.55)
    parser.add_argument("--work-dir", type=Path, default=None)
    args = parser.parse_args()

    work = args.work_dir or args.out.parent / "intro_pe_fix_work"
    work.mkdir(parents=True, exist_ok=True)

    head = work / "intro_head.mp4"
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(args.intro),
            "-t",
            str(args.keep_until),
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
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    freeze = work / "pe_atmos.png"
    extract_freeze(args.intro, min(args.keep_until - 0.3, 7.2), freeze)
    pe_png = work / "pe_clean.png"
    render_clean_pe(freeze, pe_png)
    pe_mp4 = work / "pe_clean_hold.mp4"
    still_hold(pe_png, args.intro, pe_mp4, seconds=args.pe_seconds, audio_start=args.keep_until)

    # soft xfade head → clean PE
    off = max(0.05, args.keep_until - args.xfade)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(head),
            "-i",
            str(pe_mp4),
            "-filter_complex",
            (
                f"[0:v][1:v]xfade=transition=fade:duration={args.xfade:.2f}:offset={off:.3f}[v];"
                f"[0:a][1:a]acrossfade=d={args.xfade:.2f}[a]"
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
            str(args.out),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
