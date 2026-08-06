#!/usr/bin/env python3
"""Pairwise VLM scoring for Omni-Rewriter H3 raw vs PE videos (internal track)."""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import time
from pathlib import Path

import requests

ROOT = Path("/pfs/weiyang/Omni-Rewriter/experiments/t2va-base-15s-raw-vs-pe")
SCENARIOS = [
    "s01_dialogue",
    "s02_multilingual",
    "s03_wetland",
    "s04_cyclist",
    "s05_wok",
    "s06_sneaker",
    "s07_bowling",
    "s08_jazz",
    "s09_noir",
    "s10_phone_call",
    "s11_museum_reveal",
    "s12_alley_chase",
    "s13_rooftop_orbit",
    "s14_kitchen_stations",
    "s15_concert_crashzoom",
    "s16_train_matchcut",
]
CRITERIA = [
    "prompt_adherence",
    "dialogue_lip_sync",
    "ambient_music_fidelity",
    "action_audio_sync",
    "shot_timing_continuity",
    "physical_plausibility",
    "artifact_freedom",
]


def extract_frames(video: Path, out_dir: Path, times=("2", "7", "12")) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, t in enumerate(times):
        dest = out_dir / f"f{i}_{t}s.jpg"
        if not dest.exists():
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-ss",
                    t,
                    "-i",
                    str(video),
                    "-frames:v",
                    "1",
                    "-q:v",
                    "2",
                    str(dest),
                ],
                check=True,
                capture_output=True,
            )
        paths.append(dest)
    return paths


def b64_image(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


def judge_pair(
    api_base: str,
    model: str,
    scenario_id: str,
    prompt: str,
    raw_frames: list[Path],
    pe_frames: list[Path],
) -> dict:
    content = [
        {
            "type": "text",
            "text": (
                "You compare two MiniMax-H3 T2VA outputs for the SAME user prompt.\n"
                "Arm A = RAW prompt. Arm B = Omni-Rewriter PE prompt.\n"
                "Score each criterion 0-10 for BOTH arms, then pick winner.\n"
                f"Scenario: {scenario_id}\nPrompt: {prompt}\n"
                "Criteria: " + ", ".join(CRITERIA) + "\n"
                "Return ONLY JSON: {"
                '"raw": {criterion: number, ...}, '
                '"pe": {criterion: number, ...}, '
                '"winner": "raw"|"pe"|"tie", '
                '"overall_raw": number, "overall_pe": number, '
                '"rationale": "short"}'
            ),
        }
    ]
    for label, frames in (("RAW", raw_frames), ("PE", pe_frames)):
        content.append({"type": "text", "text": f"=== {label} frames ==="})
        for frame in frames:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64_image(frame)}"},
                }
            )
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "temperature": 0.1,
        "max_tokens": 1200,
    }
    url = api_base.rstrip("/") + "/chat/completions"
    for attempt in range(4):
        try:
            resp = requests.post(url, json=payload, timeout=180)
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"].strip()
            if text.startswith("```"):
                text = text.strip("`")
                if text.lower().startswith("json"):
                    text = text[4:].strip()
            return json.loads(text)
        except Exception as exc:  # noqa: BLE001
            if attempt == 3:
                return {"error": str(exc)}
            time.sleep(2 * (attempt + 1))
    return {"error": "unreachable"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-base", default="http://127.0.0.1:8108/v1")
    ap.add_argument("--model", default="Qwen3-VL-8B-Instruct")
    ap.add_argument("--out", type=Path, default=ROOT / "eval" / "vlm_pairwise_internal.json")
    args = ap.parse_args()

    prompts = {}
    for sid in SCENARIOS:
        prompts[sid] = json.loads((ROOT / "prompts" / "raw" / f"{sid}.json").read_text())[
            "prompt"
        ]

    frame_root = ROOT / "eval" / "frames"
    rows = []
    for sid in SCENARIOS:
        raw_v = ROOT / "videos" / "raw" / f"{sid}.mp4"
        pe_v = ROOT / "videos" / "pe" / f"{sid}.mp4"
        print(f"scoring {sid}", flush=True)
        raw_f = extract_frames(raw_v, frame_root / sid / "raw")
        pe_f = extract_frames(pe_v, frame_root / sid / "pe")
        result = judge_pair(args.api_base, args.model, sid, prompts[sid], raw_f, pe_f)
        rows.append({"scenario_id": sid, "result": result})
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")

    # Aggregate
    wins = {"raw": 0, "pe": 0, "tie": 0}
    raw_scores, pe_scores = [], []
    for row in rows:
        r = row["result"]
        if "error" in r:
            continue
        w = str(r.get("winner", "tie")).lower()
        wins[w if w in wins else "tie"] += 1
        if isinstance(r.get("overall_raw"), (int, float)):
            raw_scores.append(float(r["overall_raw"]))
        if isinstance(r.get("overall_pe"), (int, float)):
            pe_scores.append(float(r["overall_pe"]))
    summary = {
        "n": len(rows),
        "wins": wins,
        "mean_overall_raw": sum(raw_scores) / len(raw_scores) if raw_scores else None,
        "mean_overall_pe": sum(pe_scores) / len(pe_scores) if pe_scores else None,
        "track": "internal_vlm_pairwise",
        "note": "Not an official MiniMax/H3 leaderboard metric.",
    }
    summary_path = ROOT / "eval" / "vlm_pairwise_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
