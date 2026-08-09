#!/usr/bin/env python3
"""Models beat without hanging-board B-roll: intro bridge → centered brand + T2V|T2I list.

Atmosphere comes from a warm freeze (intro / proof), not H3 dual-lane boards.
Assemble: proof → bridge → brand hold → GitHub endcard.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MATRIX = ROOT / "docs/promo/model_matrix.yaml"
W, H = 1344, 768
FONT = "/usr/share/fonts/truetype/comfortaa/Comfortaa-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/comfortaa/Comfortaa-Regular.ttf"


def _font(size: int, *, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    paths = (
        (FONT if bold else FONT_REG),
        FONT,
        "/usr/share/fonts/truetype/lato/Lato-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    )
    for path in paths:
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


def _atmosphere(freeze: Path, *, blur: float) -> Image.Image:
    base = Image.open(freeze).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    soft = base.filter(ImageFilter.GaussianBlur(radius=blur))
    # Warm lift so the transition does not feel like a cold slate.
    warm = Image.new("RGB", (W, H), (42, 28, 24))
    return Image.blend(soft, warm, 0.22)


def _vignette(dr: ImageDraw.ImageDraw, strength: int = 110) -> None:
    for i in range(0, 200, 4):
        a = int(strength * (1 - i / 200))
        dr.rectangle((0, 0, W, i), fill=(16, 12, 14, a))
        dr.rectangle((0, H - i, W, H), fill=(16, 12, 14, a))
        dr.rectangle((0, 0, i, H), fill=(16, 12, 14, int(a * 0.7)))
        dr.rectangle((W - i, 0, W, H), fill=(16, 12, 14, int(a * 0.7)))


def _center_wash(alpha_peak: int = 96) -> Image.Image:
    wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wdr = ImageDraw.Draw(wash)
    for radius, alpha in ((560, 22), (440, 40), (340, 62), (260, alpha_peak)):
        wdr.ellipse(
            (
                W // 2 - radius,
                H // 2 - int(radius * 0.7),
                W // 2 + radius,
                H // 2 + int(radius * 0.7),
            ),
            fill=(20, 14, 18, alpha),
        )
    return wash.filter(ImageFilter.GaussianBlur(radius=20))


def render_bridge_still(freeze: Path, out_png: Path) -> None:
    """Introductory beat: atmosphere + soft lane tease, no model inventory yet."""
    soft = _atmosphere(freeze, blur=5.5)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(overlay)
    _vignette(dr, strength=90)

    title = _font(42)
    sub = _font(22, bold=False)
    lane = _font(26)
    cx, cy = W // 2, H // 2 - 36

    dr.text(
        (cx + 1.5, cy + 1.5), "Open across models", font=title, fill=(40, 26, 20, 140), anchor="mm"
    )
    dr.text((cx, cy), "Open across models", font=title, fill=(255, 250, 245, 245), anchor="mm")
    dr.text(
        (cx, cy + 48),
        "prompt expansion · one harness",
        font=sub,
        fill=(230, 216, 205, 210),
        anchor="mm",
    )
    # Soft T2V | T2I tease — typography only, not hanging boards
    dr.text((cx - 90, cy + 118), "T2V", font=lane, fill=(255, 188, 176, 230), anchor="mm")
    dr.text((cx, cy + 118), "·", font=lane, fill=(220, 210, 200, 180), anchor="mm")
    dr.text((cx + 90, cy + 118), "T2I", font=lane, fill=(180, 236, 212, 230), anchor="mm")

    composed = Image.alpha_composite(soft.convert("RGBA"), _center_wash(78))
    composed = Image.alpha_composite(composed, overlay)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    composed.convert("RGB").save(out_png)


def render_title_still(
    freeze: Path,
    matrix_path: Path,
    out_png: Path,
    *,
    with_list: bool = True,
) -> None:
    matrix = yaml.safe_load(matrix_path.read_text())
    video = [m["name"] for m in matrix["video"][:6]]
    image = [m["name"] for m in matrix["image"][:6]]

    soft = _atmosphere(freeze, blur=3.2)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(overlay)
    _vignette(dr, strength=105)

    brand = _font(76)
    sub = _font(22, bold=False)
    lane = _font(20)
    body = _font(18)

    cx, cy = W // 2, 248 if with_list else 340
    dr.text((cx + 2, cy + 2), "Omni-Rewriter", font=brand, fill=(40, 24, 18, 150), anchor="mm")
    dr.text((cx, cy), "Omni-Rewriter", font=brand, fill=(255, 252, 248, 252), anchor="mm")
    dr.text(
        (cx, cy + 54),
        "one harness across video and image",
        font=sub,
        fill=(232, 220, 210, 215),
        anchor="mm",
    )

    if with_list:
        left_x, right_x = W // 2 - 220, W // 2 + 220
        list_top = 350
        dr.text((left_x, list_top), "T2V", font=lane, fill=(255, 190, 178, 235), anchor="mm")
        dr.text((right_x, list_top), "T2I", font=lane, fill=(184, 240, 216, 235), anchor="mm")
        for i, name in enumerate(video):
            dr.text(
                (left_x, list_top + 34 + i * 28),
                name,
                font=body,
                fill=(255, 250, 245, 235),
                anchor="mm",
            )
        for i, name in enumerate(image):
            dr.text(
                (right_x, list_top + 34 + i * 28),
                name,
                font=body,
                fill=(255, 250, 245, 235),
                anchor="mm",
            )

    composed = Image.alpha_composite(soft.convert("RGBA"), _center_wash(96))
    composed = Image.alpha_composite(composed, overlay)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    composed.convert("RGB").save(out_png)


def still_to_hold(
    png: Path,
    audio_src: Path,
    dest: Path,
    *,
    seconds: float,
    fade_in: float,
    audio_start: float,
    zoom_rate: float = 0.0018,
    sway: float = 7.0,
) -> None:
    frames = max(int(seconds * 24), 24)
    z_expr = f"min(1.06,1+{zoom_rate}*on)"
    x_expr = f"iw/2-(iw/zoom/2)+{sway}*sin(on/16)"
    y_expr = "(ih-ih/zoom)/2+3*sin(on/20)"
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
                f"[0:v]scale=1500:858,zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':"
                f"d={frames}:s={W}x{H}:fps=24,format=yuv420p,"
                f"fade=t=in:st=0:d={fade_in:.2f}[v];"
                f"[1:a]atrim=start={audio_start:.2f}:duration={seconds},asetpts=PTS-STARTPTS,"
                f"afade=t=in:st=0:d={min(fade_in, 0.6):.2f},"
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
    parser.add_argument(
        "--atmosphere",
        type=Path,
        default=None,
        help="Warm source clip for background freeze (intro preferred)",
    )
    parser.add_argument(
        "--broll",
        type=Path,
        default=None,
        help="Deprecated alias for --atmosphere (hanging-board B-roll no longer used)",
    )
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--freeze-at", type=float, default=11.5)
    parser.add_argument("--out-still", type=Path, required=True)
    parser.add_argument("--out-hold", type=Path, required=True)
    parser.add_argument(
        "--out-bridge",
        type=Path,
        default=None,
        help="Introductory transition clip before the brand+list hold",
    )
    parser.add_argument("--bridge-seconds", type=float, default=2.2)
    parser.add_argument("--hold-seconds", type=float, default=3.8)
    parser.add_argument("--fade-in", type=float, default=0.75)
    parser.add_argument("--brand-only", action="store_true", help="Hero brand without model list")
    args = parser.parse_args()

    atmosphere = args.atmosphere or args.broll
    if atmosphere is None:
        raise SystemExit("provide --atmosphere (preferred) or --broll")

    freeze = args.out_still.with_name("models_brand_freeze.png")
    extract_freeze(atmosphere, args.freeze_at, freeze)

    if args.out_bridge is not None:
        bridge_still = args.out_still.with_name("models_bridge_still.png")
        render_bridge_still(freeze, bridge_still)
        still_to_hold(
            bridge_still,
            atmosphere,
            args.out_bridge,
            seconds=args.bridge_seconds,
            fade_in=0.55,
            audio_start=max(0.0, args.freeze_at - 1.0),
            zoom_rate=0.0024,
            sway=9.0,
        )
        print(f"wrote {args.out_bridge}")

    render_title_still(freeze, args.matrix, args.out_still, with_list=not args.brand_only)
    still_to_hold(
        args.out_still,
        atmosphere,
        args.out_hold,
        seconds=args.hold_seconds,
        fade_in=args.fade_in,
        audio_start=max(0.0, args.freeze_at + 0.5),
        zoom_rate=0.0015,
        sway=6.0,
    )
    print(f"wrote {args.out_still}")
    print(f"wrote {args.out_hold}")


if __name__ == "__main__":
    main()
