#!/usr/bin/env python3
"""Render T2V / T2I model-name plates for the promo (accurate text, no Seedance)."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MATRIX = ROOT / "docs/promo/model_matrix.yaml"
W, H = 1344, 768


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (
        "/usr/share/fonts/truetype/comfortaa/Comfortaa-Bold.ttf",
        "/usr/share/fonts/truetype/lato/Lato-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def _status_color(status: str) -> tuple[int, int, int]:
    return {
        "PE": (124, 255, 203),
        "adapter": (255, 214, 102),
        "unverified": (200, 200, 210),
        "wanted": (180, 180, 195),
    }.get(status, (220, 220, 220))


def render_lane_plate(
    title: str,
    models: list[dict[str, str]],
    accent: tuple[int, int, int],
) -> Image.Image:
    img = Image.new("RGB", (W, H), (28, 24, 34))
    draw = ImageDraw.Draw(img)
    # soft panels
    draw.rounded_rectangle((48, 48, W - 48, H - 48), radius=28, fill=(42, 36, 48))
    draw.rounded_rectangle((64, 64, W - 64, 150), radius=18, fill=accent)
    title_font = _font(42)
    body = _font(28)
    small = _font(18)
    draw.text((88, 88), title, fill=(20, 18, 24), font=title_font)

    cols = 2
    rows = (len(models) + cols - 1) // cols
    grid_top = 180
    cell_w = (W - 160) // cols
    cell_h = min(88, (H - grid_top - 80) // max(rows, 1))
    for i, model in enumerate(models):
        r, c = divmod(i, cols)
        x0 = 80 + c * cell_w
        y0 = grid_top + r * (cell_h + 12)
        x1 = x0 + cell_w - 16
        y1 = y0 + cell_h
        draw.rounded_rectangle((x0, y0, x1, y1), radius=16, fill=(55, 48, 62))
        draw.text((x0 + 20, y0 + 18), model["name"], fill=(245, 245, 248), font=body)
        sc = _status_color(model["status"])
        draw.text((x0 + 20, y0 + 52), model["status"], fill=sc, font=small)
    return img


def render_combo_plate(matrix: dict) -> Image.Image:
    """Both lanes visible at once — prevents T2I-only collapse."""
    img = Image.new("RGB", (W, H), (22, 18, 28))
    draw = ImageDraw.Draw(img)
    title_font = _font(36)
    body = _font(22)
    small = _font(16)
    draw.text((64, 36), "T2V  ·  Video", fill=(255, 180, 168), font=title_font)
    draw.text((W // 2 + 24, 36), "T2I  ·  Image", fill=(184, 240, 216), font=title_font)

    def draw_col(models: list[dict[str, str]], x0: int, accent: tuple[int, int, int]) -> None:
        draw.rounded_rectangle((x0, 90, x0 + W // 2 - 56, H - 48), radius=22, fill=(40, 34, 48))
        y = 110
        for model in models:
            draw.rounded_rectangle((x0 + 16, y, x0 + W // 2 - 72, y + 58), radius=12, fill=(52, 46, 60))
            draw.rectangle((x0 + 16, y, x0 + 22, y + 58), fill=accent)
            draw.text((x0 + 36, y + 10), model["name"], fill=(245, 245, 248), font=body)
            draw.text((x0 + 36, y + 34), model["status"], fill=_status_color(model["status"]), font=small)
            y += 68

    draw_col(matrix["video"], 40, (255, 180, 168))
    draw_col(matrix["image"], W // 2 + 16, (184, 240, 216))
    return img


def render_elegant_overlay(matrix: dict) -> Image.Image:
    """Transparent name chips for one soft burn-in over H3 B-roll (not a spreadsheet cut)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # light vignette so chips read, H3 scene still visible
    for i in range(0, 120, 4):
        a = int(70 * (1 - i / 120))
        draw.rectangle((0, 0, W, i), fill=(20, 16, 24, a))
        draw.rectangle((0, H - i, W, H), fill=(20, 16, 24, a))

    title = _font(30)
    body = _font(20)
    tiny = _font(14)
    draw.text((72, 40), "T2V", fill=(255, 190, 178, 230), font=title)
    draw.text((W // 2 + 40, 40), "T2I", fill=(184, 240, 216, 230), font=title)

    def chips(models: list[dict[str, str]], x0: int, accent: tuple[int, int, int]) -> None:
        y = 96
        for model in models:
            name = model["name"]
            # measure chip
            bbox = draw.textbbox((0, 0), name, font=body)
            tw = bbox[2] - bbox[0]
            chip_w = min(520, max(220, tw + 48))
            chip_h = 44
            draw.rounded_rectangle(
                (x0, y, x0 + chip_w, y + chip_h),
                radius=14,
                fill=(255, 255, 255, 48),
                outline=(*accent, 160),
                width=2,
            )
            draw.ellipse((x0 + 14, y + 16, x0 + 26, y + 28), fill=(*_status_color(model["status"]), 230))
            draw.text((x0 + 36, y + 10), name, fill=(255, 255, 255, 235), font=body)
            draw.text((x0 + chip_w - 70, y + 14), model["status"], fill=(230, 230, 235, 180), font=tiny)
            y += 56

    chips(matrix["video"], 56, (255, 180, 168))
    chips(matrix["image"], W // 2 + 24, (184, 240, 216))
    return img


def png_to_mp4(png: Path, mp4: Path, seconds: float, fps: int = 24) -> None:
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(png),
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-t",
            str(seconds),
            "-r",
            str(fps),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-shortest",
            str(mp4),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=4.0)
    args = parser.parse_args()

    matrix = yaml.safe_load(args.matrix.read_text())
    args.out_dir.mkdir(parents=True, exist_ok=True)

    t2v = render_lane_plate("T2V  ·  Video models", matrix["video"], (255, 180, 168))
    t2i = render_lane_plate("T2I  ·  Image models", matrix["image"], (184, 240, 216))
    combo = render_combo_plate(matrix)
    overlay = render_elegant_overlay(matrix)

    for name, img in (("plate_t2v", t2v), ("plate_t2i", t2i), ("plate_combo", combo)):
        png = args.out_dir / f"{name}.png"
        mp4 = args.out_dir / f"{name}.mp4"
        img.save(png)
        png_to_mp4(png, mp4, args.seconds)
        print(f"wrote {mp4}")

    overlay_png = args.out_dir / "plate_overlay.png"
    overlay.save(overlay_png)
    print(f"wrote {overlay_png}")


if __name__ == "__main__":
    main()
