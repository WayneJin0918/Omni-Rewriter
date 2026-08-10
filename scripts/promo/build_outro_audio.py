#!/usr/bin/env python3
"""Build designed outro VO + intro-style BGM bed for the models/end act."""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
from pathlib import Path

DEFAULT_SCRIPT = (
    "Star Omni-Rewriter on GitHub. We support MiniMax-H3, Seedream, and "
    "Qwen Image — plus adapters across video and image."
)


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


async def _synthesize(text: str, voice: str, dest: Path, *, rate: str) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    await communicate.save(str(dest))


def synthesize_vo(text: str, voice: str, dest: Path, *, rate: str = "-5%") -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_synthesize(text, voice, dest, rate=rate))


def mix_vo_with_bgm(
    vo: Path,
    atmosphere: Path,
    dest: Path,
    *,
    seconds: float,
    bgm_start: float,
    bgm_vol: float,
    vo_vol: float,
    fade_out: float = 1.0,
) -> None:
    """Mix VO with optional intro-style BGM. H3 beds already include music — use bgm_vol=0."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    fo = max(0.25, min(fade_out, max(0.25, seconds - 0.05)))
    fade_st = max(0.0, seconds - fo)
    # H3 t2va audio already carries pluck BGM; do not amix a second bed (avoids overlap).
    if bgm_vol <= 0.001:
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(vo),
                "-filter_complex",
                (
                    f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,"
                    f"volume={vo_vol:.2f},apad=whole_dur={seconds:.3f},"
                    f"afade=t=in:st=0:d=0.12,afade=t=out:st={fade_st:.2f}:d={fo:.2f},"
                    f"alimiter=limit=0.95[a]"
                ),
                "-map",
                "[a]",
                "-t",
                str(seconds),
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                str(dest),
            ]
        )
        return
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(vo),
            "-i",
            str(atmosphere),
            "-filter_complex",
            (
                f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,"
                f"volume={vo_vol:.2f},apad=whole_dur={seconds:.3f},"
                f"afade=t=in:st=0:d=0.12,afade=t=out:st={fade_st:.2f}:d={fo:.2f}[vo];"
                f"[1:a]atrim=start={bgm_start:.2f}:duration={seconds:.3f},asetpts=PTS-STARTPTS,"
                f"aformat=sample_rates=48000:channel_layouts=stereo,volume={bgm_vol:.2f},"
                f"apad=whole_dur={seconds:.3f},"
                f"afade=t=in:st=0:d=0.35,afade=t=out:st={fade_st:.2f}:d={fo:.2f}[bg];"
                f"[bg][vo]amix=inputs=2:duration=first:dropout_transition=0,"
                f"alimiter=limit=0.95[a]"
            ),
            "-map",
            "[a]",
            "-t",
            str(seconds),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(dest),
        ]
    )


def mux_audio_segment(
    video: Path, audio: Path, dest: Path, *, audio_start: float, seconds: float
) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video),
            "-ss",
            f"{audio_start:.3f}",
            "-i",
            str(audio),
            "-map",
            "0:v",
            "-map",
            "1:a",
            "-t",
            str(seconds),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(dest),
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--atmosphere", type=Path, required=True, help="Intro clip for BGM bed")
    parser.add_argument(
        "--finale-video", type=Path, required=True, help="Silent/designed models finale"
    )
    parser.add_argument("--end-video", type=Path, required=True, help="Endcard video")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--out-finale", type=Path, required=True)
    parser.add_argument("--out-end", type=Path, required=True)
    parser.add_argument("--script", type=str, default=DEFAULT_SCRIPT)
    parser.add_argument("--voice", type=str, default="en-US-JennyNeural")
    parser.add_argument("--rate", type=str, default="-5%")
    parser.add_argument(
        "--vo-audio",
        type=Path,
        default=None,
        help="Use an existing VO/H3 clip audio instead of edge-tts (matches intro narrator)",
    )
    parser.add_argument("--bgm-start", type=float, default=2.2)
    parser.add_argument("--bgm-vol", type=float, default=0.22)
    parser.add_argument("--vo-vol", type=float, default=1.05)
    parser.add_argument(
        "--tail-silence",
        type=float,
        default=0.0,
        help="Optional pad after VO (seconds). Prefer 0 for H3 beds that already settle.",
    )
    parser.add_argument(
        "--fade-out",
        type=float,
        default=1.0,
        help="Audio fade-out length at the end of the outro bed",
    )
    parser.add_argument(
        "--min-seconds",
        type=float,
        default=None,
        help="Pad mix to at least finale+end duration (default: auto)",
    )
    args = parser.parse_args()

    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    vo_raw = out / "outro_vo_raw.wav"
    if args.vo_audio is not None:
        # Prefer H3 narrator audio so timbre matches the intro VO.
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(args.vo_audio),
                "-vn",
                "-ac",
                "2",
                "-ar",
                "48000",
                "-c:a",
                "pcm_s16le",
                str(vo_raw),
            ]
        )
    else:
        mp3 = out / "outro_vo_raw.mp3"
        synthesize_vo(args.script, args.voice, mp3, rate=args.rate)
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(mp3),
                "-ac",
                "2",
                "-ar",
                "48000",
                "-c:a",
                "pcm_s16le",
                str(vo_raw),
            ]
        )

    finale_d = dur(args.finale_video)
    end_d = dur(args.end_video)
    need = finale_d + end_d
    if args.min_seconds is not None:
        need = max(need, args.min_seconds)
    vo_d = dur(vo_raw)
    # Optional post-VO pad (default 0). Fade-out rides inside the clip — no dead silence tail.
    seconds = max(need, vo_d + max(0.0, args.tail_silence))

    mix = out / "outro_vo_bgm.m4a"
    mix_vo_with_bgm(
        vo_raw,
        args.atmosphere,
        mix,
        seconds=seconds,
        bgm_start=args.bgm_start,
        bgm_vol=args.bgm_vol,
        vo_vol=args.vo_vol,
        fade_out=args.fade_out,
    )

    # If VO needs more time than current endcard, extend endcard hold.
    end_src = args.end_video
    if seconds > need + 0.05:
        extra = seconds - finale_d
        extended = out / "end_extended.mp4"
        run(
            [
                "ffmpeg",
                "-y",
                "-stream_loop",
                "-1",
                "-i",
                str(args.end_video),
                "-t",
                f"{extra:.3f}",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-an",
                str(extended),
            ]
        )
        # Restore silent stereo for mux helper consistency
        end_silent = out / "end_extended_a.mp4"
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(extended),
                "-f",
                "lavfi",
                "-i",
                "anullsrc=channel_layout=stereo:sample_rate=48000",
                "-map",
                "0:v",
                "-map",
                "1:a",
                "-t",
                f"{extra:.3f}",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-shortest",
                str(end_silent),
            ]
        )
        end_src = end_silent
        end_d = extra

    mux_audio_segment(args.finale_video, mix, args.out_finale, audio_start=0.0, seconds=finale_d)
    mux_audio_segment(end_src, mix, args.out_end, audio_start=finale_d, seconds=end_d)

    # One continuous outro (video soft cut + unbroken VO/BGM) for assemble --no-endcard.
    out_full = out / "outro_full.mp4"
    off = max(0.05, finale_d - 0.3)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(args.out_finale),
            "-i",
            str(args.out_end),
            "-i",
            str(mix),
            "-filter_complex",
            (
                f"[0:v][1:v]xfade=transition=fade:duration=0.30:offset={off:.3f},format=yuv420p[v];"
                f"[2:a]aformat=sample_rates=48000:channel_layouts=stereo,"
                f"atrim=0:{finale_d + end_d - 0.3:.3f},asetpts=PTS-STARTPTS[a]"
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
            "192k",
            str(out_full),
        ]
    )

    meta = {
        "script": args.script,
        "voice": args.voice,
        "vo_seconds": vo_d,
        "mix_seconds": seconds,
        "finale_seconds": finale_d,
        "end_seconds": end_d,
        "mix": str(mix),
        "outro_full": str(out_full),
    }
    (out / "outro_audio.meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
