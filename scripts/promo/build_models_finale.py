#!/usr/bin/env python3
"""Designed models finale: bridge → brand hero → staggered T2V|T2I lanes (no hanging B-roll)."""

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
    for path in (
        FONT if bold else FONT_REG,
        FONT,
        "/usr/share/fonts/truetype/lato/Lato-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
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


def _atmosphere(freeze: Path, *, blur: float, warm: float = 0.28) -> Image.Image:
    base = Image.open(freeze).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    soft = base.filter(ImageFilter.GaussianBlur(radius=blur))
    tint = Image.new("RGB", (W, H), (48, 30, 26))
    return Image.blend(soft, tint, warm)


def _vignette(dr: ImageDraw.ImageDraw, strength: int = 120) -> None:
    for i in range(0, 220, 4):
        a = int(strength * (1 - i / 220))
        dr.rectangle((0, 0, W, i), fill=(14, 10, 12, a))
        dr.rectangle((0, H - i, W, H), fill=(14, 10, 12, a))
        dr.rectangle((0, 0, i, H), fill=(14, 10, 12, int(a * 0.7)))
        dr.rectangle((W - i, 0, W, H), fill=(14, 10, 12, int(a * 0.7)))


def _wash(peak: int = 100) -> Image.Image:
    wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wdr = ImageDraw.Draw(wash)
    for radius, alpha in ((580, 24), (460, 44), (360, 70), (270, peak)):
        wdr.ellipse(
            (
                W // 2 - radius,
                H // 2 - int(radius * 0.68),
                W // 2 + radius,
                H // 2 + int(radius * 0.68),
            ),
            fill=(18, 12, 16, alpha),
        )
    # soft light bloom top-center
    bloom = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bdr = ImageDraw.Draw(bloom)
    bdr.ellipse((W // 2 - 280, -40, W // 2 + 280, 220), fill=(255, 210, 180, 28))
    wash = Image.alpha_composite(wash, bloom.filter(ImageFilter.GaussianBlur(radius=36)))
    return wash.filter(ImageFilter.GaussianBlur(radius=16))


def render_bridge(freeze: Path, out_png: Path) -> None:
    soft = _atmosphere(freeze, blur=6.0, warm=0.3)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(overlay)
    _vignette(dr, 100)
    title, sub, lane = _font(44), _font(22, bold=False), _font(28)
    cx, cy = W // 2, H // 2 - 40
    # thin accent rule
    dr.rounded_rectangle((cx - 48, cy - 70, cx + 48, cy - 66), radius=2, fill=(255, 200, 180, 160))
    dr.text((cx + 1.5, cy + 1.5), "Open across models", font=title, fill=(40, 26, 20, 150), anchor="mm")
    dr.text((cx, cy), "Open across models", font=title, fill=(255, 250, 245, 250), anchor="mm")
    dr.text((cx, cy + 50), "prompt expansion · one harness", font=sub, fill=(230, 216, 205, 215), anchor="mm")
    dr.text((cx - 96, cy + 124), "T2V", font=lane, fill=(255, 188, 176, 240), anchor="mm")
    dr.text((cx, cy + 124), "·", font=lane, fill=(220, 210, 200, 190), anchor="mm")
    dr.text((cx + 96, cy + 124), "T2I", font=lane, fill=(180, 236, 212, 240), anchor="mm")
    composed = Image.alpha_composite(soft.convert("RGBA"), _wash(82))
    composed = Image.alpha_composite(composed, overlay)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    composed.convert("RGB").save(out_png)


def render_brand_hero(freeze: Path, out_png: Path) -> None:
    soft = _atmosphere(freeze, blur=3.8, warm=0.26)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(overlay)
    _vignette(dr, 115)
    brand, sub = _font(82), _font(24, bold=False)
    cx, cy = W // 2, H // 2 - 20
    dr.rounded_rectangle((cx - 56, cy - 78, cx + 56, cy - 74), radius=2, fill=(255, 200, 180, 150))
    dr.text((cx + 2, cy + 2), "Omni-Rewriter", font=brand, fill=(40, 24, 18, 155), anchor="mm")
    dr.text((cx, cy), "Omni-Rewriter", font=brand, fill=(255, 252, 248, 255), anchor="mm")
    dr.text(
        (cx, cy + 62),
        "one harness across video and image",
        font=sub,
        fill=(232, 220, 210, 220),
        anchor="mm",
    )
    composed = Image.alpha_composite(soft.convert("RGBA"), _wash(100))
    composed = Image.alpha_composite(composed, overlay)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    composed.convert("RGB").save(out_png)


def render_lanes(freeze: Path, matrix_path: Path, out_png: Path) -> None:
    matrix = yaml.safe_load(matrix_path.read_text())
    video = [m["name"] for m in matrix["video"][:6]]
    image = [m["name"] for m in matrix["image"][:6]]
    soft = _atmosphere(freeze, blur=3.4, warm=0.24)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(overlay)
    _vignette(dr, 110)
    brand, sub, lane, body = _font(56), _font(20, bold=False), _font(20), _font(18)
    cx = W // 2
    dr.text((cx + 1.5, 168), "Omni-Rewriter", font=brand, fill=(40, 24, 18, 130), anchor="mm")
    dr.text((cx, 166), "Omni-Rewriter", font=brand, fill=(255, 252, 248, 250), anchor="mm")
    dr.text((cx, 214), "one harness across video and image", font=sub, fill=(232, 220, 210, 210), anchor="mm")
    left_x, right_x, list_top = W // 2 - 230, W // 2 + 230, 280
    # soft column plates
    for x0, x1, fill in (
        (left_x - 150, left_x + 150, (255, 180, 160, 22)),
        (right_x - 150, right_x + 150, (160, 230, 200, 22)),
    ):
        dr.rounded_rectangle((x0, list_top - 18, x1, list_top + 34 + 6 * 28 + 16), radius=18, fill=fill)
    dr.text((left_x, list_top), "T2V", font=lane, fill=(255, 190, 178, 240), anchor="mm")
    dr.text((right_x, list_top), "T2I", font=lane, fill=(184, 240, 216, 240), anchor="mm")
    for i, name in enumerate(video):
        dr.text((left_x, list_top + 36 + i * 28), name, font=body, fill=(255, 250, 245, 240), anchor="mm")
    for i, name in enumerate(image):
        dr.text((right_x, list_top + 36 + i * 28), name, font=body, fill=(255, 250, 245, 240), anchor="mm")
    composed = Image.alpha_composite(soft.convert("RGBA"), _wash(92))
    composed = Image.alpha_composite(composed, overlay)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    composed.convert("RGB").save(out_png)


def still_to_clip(
    png: Path,
    audio_src: Path,
    dest: Path,
    *,
    seconds: float,
    fade_in: float,
    audio_start: float,
    zoom_rate: float,
    sway: float,
    fade_out: float = 0.0,
) -> None:
    frames = max(int(seconds * 24), 24)
    z_expr = f"min(1.07,1+{zoom_rate}*on)"
    x_expr = f"iw/2-(iw/zoom/2)+{sway}*sin(on/15)"
    y_expr = "(ih-ih/zoom)/2+3*sin(on/19)"
    fade_out_f = ""
    if fade_out > 0:
        st = max(0.0, seconds - fade_out)
        fade_out_f = f",fade=t=out:st={st:.2f}:d={fade_out:.2f}"
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
                f"[0:v]scale=1520:868,zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':"
                f"d={frames}:s={W}x{H}:fps=24,format=yuv420p,"
                f"fade=t=in:st=0:d={fade_in:.2f}{fade_out_f}[v];"
                f"[1:a]atrim=start={audio_start:.2f}:duration={seconds},asetpts=PTS-STARTPTS,"
                f"afade=t=in:st=0:d={min(fade_in, 0.55):.2f},"
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


def _dur(path: Path) -> float:
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


def xfade_video(a: Path, b: Path, dest: Path, *, duration: float = 0.45) -> None:
    """Soft xfade video only (audio added once for the whole finale)."""
    off = max(0.05, _dur(a) - duration)
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(a),
            "-i",
            str(b),
            "-filter_complex",
            f"[0:v][1:v]xfade=transition=fade:duration={duration:.2f}:offset={off:.3f},format=yuv420p[v]",
            "-map",
            "[v]",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(dest),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def mux_continuous_audio(
    video: Path,
    audio_src: Path,
    dest: Path,
    *,
    audio_start: float,
) -> None:
    """One continuous bed — avoids repeating the same intro music phrase per beat."""
    seconds = _dur(video)
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video),
            "-i",
            str(audio_src),
            "-filter_complex",
            (
                f"[1:a]atrim=start={audio_start:.2f}:duration={seconds:.3f},asetpts=PTS-STARTPTS,"
                f"afade=t=in:st=0:d=0.4,afade=t=out:st={max(0.0, seconds - 0.55):.2f}:d=0.55,"
                f"aformat=sample_rates=48000:channel_layouts=stereo[a]"
            ),
            "-map",
            "0:v",
            "-map",
            "[a]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-shortest",
            str(dest),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--atmosphere", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--freeze-at", type=float, default=11.5)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--bridge-seconds", type=float, default=2.2)
    parser.add_argument("--brand-seconds", type=float, default=2.6)
    parser.add_argument("--lanes-seconds", type=float, default=3.6)
    parser.add_argument(
        "--audio-start",
        type=float,
        default=None,
        help="Continuous bed start in atmosphere clip (default: freeze-at - 0.5)",
    )
    parser.add_argument("--out-finale", type=Path, required=True)
    args = parser.parse_args()

    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    freeze = out / "models_finale_freeze.png"
    extract_freeze(args.atmosphere, args.freeze_at, freeze)

    bridge_png = out / "finale_bridge.png"
    brand_png = out / "finale_brand.png"
    lanes_png = out / "finale_lanes.png"
    render_bridge(freeze, bridge_png)
    render_brand_hero(freeze, brand_png)
    render_lanes(freeze, args.matrix, lanes_png)

    # Silent video beds — music is muxed once at the end (no phrase repeats).
    silent = out / "_silent.wav"
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-t",
            "1",
            str(silent),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    bridge_mp4 = out / "seg_bridge.mp4"
    brand_mp4 = out / "seg_brand.mp4"
    lanes_mp4 = out / "seg_lanes.mp4"
    still_to_clip(
        bridge_png,
        silent,
        bridge_mp4,
        seconds=args.bridge_seconds,
        fade_in=0.4,
        audio_start=0.0,
        zoom_rate=0.0030,
        sway=9.0,
    )
    still_to_clip(
        brand_png,
        silent,
        brand_mp4,
        seconds=args.brand_seconds,
        fade_in=0.5,
        audio_start=0.0,
        zoom_rate=0.0020,
        sway=6.0,
    )
    still_to_clip(
        brand_png,
        silent,
        out / "seg_lanes_base.mp4",
        seconds=args.lanes_seconds,
        fade_in=0.15,
        audio_start=0.0,
        zoom_rate=0.0016,
        sway=5.0,
    )
    still_to_clip(
        lanes_png,
        silent,
        out / "seg_lanes_full.mp4",
        seconds=args.lanes_seconds,
        fade_in=0.01,
        audio_start=0.0,
        zoom_rate=0.0016,
        sway=5.0,
    )
    # Faster stagger (~0.55s) so the list doesn't linger empty.
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(out / "seg_lanes_base.mp4"),
            "-i",
            str(out / "seg_lanes_full.mp4"),
            "-filter_complex",
            (
                "[1:v]format=yuva420p,fade=t=in:st=0.55:d=0.7:alpha=1[ov];"
                "[0:v][ov]overlay=0:0:format=auto,format=yuv420p[v]"
            ),
            "-map",
            "[v]",
            "-an",
            "-t",
            str(args.lanes_seconds),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(lanes_mp4),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    mid = out / "finale_bridge_brand.mp4"
    video_only = out / "finale_video_only.mp4"
    xfade_video(bridge_mp4, brand_mp4, mid, duration=0.4)
    xfade_video(mid, lanes_mp4, video_only, duration=0.45)
    audio_start = (
        args.audio_start if args.audio_start is not None else max(0.0, args.freeze_at - 0.5)
    )
    mux_continuous_audio(video_only, args.atmosphere, args.out_finale, audio_start=audio_start)
    print(f"wrote {args.out_finale}")
    for p in (bridge_mp4, brand_mp4, lanes_mp4):
        print(f"wrote {p}")


if __name__ == "__main__":
    main()
