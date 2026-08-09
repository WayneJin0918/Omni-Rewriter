#!/usr/bin/env python3
"""Burn model names onto the hanging T2V/T2I slats of a frozen models B-roll frame."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MATRIX = ROOT / "docs/promo/model_matrix.yaml"
W, H = 1344, 768

# Tuned for the v6 dual hanging-board composition at ~6.2s.
LEFT_X0, LEFT_X1 = 508, 652
RIGHT_X0, RIGHT_X1 = 768, 922
# 8 body slats under T2V / T2I headers (edge-detected on freeze @ 6.2s).
Y_BANDS = [
    (142, 192),
    (200, 248),
    (256, 302),
    (310, 360),
    (368, 415),
    (423, 472),
    (480, 523),
    (532, 584),
]
# Keep header + 8 named slats only. Empty boards begin ~588 on the freeze.
CROP_TOP = 72
CROP_BOTTOM = 588


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (
        "/usr/share/fonts/truetype/comfortaa/Comfortaa-Bold.ttf",
        "/usr/share/fonts/truetype/lato/Lato-Bold.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def _fit_font(draw: ImageDraw.ImageDraw, text: str, max_w: int, prefer: int = 23) -> ImageFont.ImageFont:
    for size in range(prefer, 13, -1):
        ff = _font(size)
        bbox = draw.textbbox((0, 0), text, font=ff)
        if bbox[2] - bbox[0] <= max_w:
            return ff
    return _font(14)


def burn(frame: Path, matrix_path: Path, out_png: Path) -> None:
    matrix = yaml.safe_load(matrix_path.read_text())
    video = [m["name"] for m in matrix["video"]]
    image = [m["name"] for m in matrix["image"]]
    base = Image.open(frame).convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(overlay)

    def draw_name(x0: int, y0: int, x1: int, y1: int, text: str) -> None:
        max_w = (x1 - x0) - 20
        ff = _fit_font(dr, text, max_w, prefer=23)
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2 + 1.5  # Comfortaa sits slightly high; nudge down on glass
        # soft readable plate inset (very light)
        inset = 6
        dr.rounded_rectangle(
            (x0 + inset, y0 + inset, x1 - inset, y1 - inset),
            radius=8,
            fill=(255, 248, 240, 32),
        )
        # engraved stack: soft shadow + crisp white, truly centered
        dr.text((cx + 1.0, cy + 1.0), text, font=ff, fill=(50, 32, 22, 120), anchor="mm")
        dr.text((cx, cy), text, font=ff, fill=(255, 255, 255, 252), anchor="mm")

    for i, name in enumerate(video[:8]):
        y0, y1 = Y_BANDS[i]
        draw_name(LEFT_X0, y0, LEFT_X1, y1, name)
    for i, name in enumerate(image[:8]):
        y0, y1 = Y_BANDS[i]
        draw_name(RIGHT_X0, y0, RIGHT_X1, y1, name)

    composed = Image.alpha_composite(base, overlay)
    # Drop empty lower boards, then cover-scale (uniform) into 16:9.
    strip = composed.crop((0, CROP_TOP, W, CROP_BOTTOM))
    sw, sh = strip.size
    scale = max(W / sw, H / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    scaled = strip.resize((nw, nh), Image.Resampling.LANCZOS)
    ox = (nw - W) // 2
    # Prefer keeping the bottom of the strip (last names) when nh > H.
    oy = max(0, nh - H)
    cover = scaled.crop((ox, oy, ox + W, oy + H))
    cover = cover.filter(ImageFilter.UnsharpMask(radius=0.7, percent=70, threshold=2))

    out_png.parent.mkdir(parents=True, exist_ok=True)
    cover.convert("RGB").save(out_png)


def still_to_hold(png: Path, audio_src: Path, dest: Path, seconds: float = 2.8) -> None:
    """Short Ken Burns — gentle push-in + sway; keep last named slats fully in frame."""
    frames = max(int(seconds * 24), 24)
    # Mild push-in + horizontal sway; y locked near bottom so last names never clip.
    z_expr = "min(1.05,1+0.0016*on)"
    x_expr = "iw/2-(iw/zoom/2)+12*sin(on/12)"
    y_expr = "ih-ih/zoom"
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
                f"[0:v]scale=1600:914,zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':"
                f"d={frames}:s={W}x{H}:fps=24,format=yuv420p[v];"
                f"[1:a]atrim=start=6:duration={seconds},asetpts=PTS-STARTPTS,"
                f"aformat=sample_rates=48000:channel_layouts=stereo[a]"
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
    parser.add_argument("--broll", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--freeze-at", type=float, default=6.2)
    parser.add_argument("--out-still", type=Path, required=True)
    parser.add_argument("--out-hold", type=Path, required=True)
    parser.add_argument("--hold-seconds", type=float, default=2.8)
    args = parser.parse_args()

    freeze = args.out_still.with_name("models_freeze.png")
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(args.freeze_at),
            "-i",
            str(args.broll),
            "-update",
            "1",
            "-frames:v",
            "1",
            str(freeze),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    burn(freeze, args.matrix, args.out_still)
    still_to_hold(args.out_still, args.broll, args.out_hold, args.hold_seconds)
    print(f"wrote {args.out_still}")
    print(f"wrote {args.out_hold}")


if __name__ == "__main__":
    main()
