#!/usr/bin/env python3
"""Reproducible raw-vs-PE MiniMax-H3 comparison (base + camera/cut stress cases)."""

from __future__ import annotations

import argparse
import asyncio
import html
import json
import subprocess
import time
from pathlib import Path
from typing import Any

import httpx

from omni_rewriter.agent import RewriteAgent, RewriteAgentConfig
from omni_rewriter.backends import ChatBackendConfig, OpenAICompatibleBackend
from omni_rewriter.media_input import MediaPreparer
from omni_rewriter.models import RewriteRequest

ROOT = Path(__file__).resolve().parent
DURATION = 15
TARGET = {"short_edge": 768, "aspect_ratio": "16:9", "duration_seconds": DURATION}

SCENARIOS = [
    {
        "id": "s01_dialogue",
        "category": "english_dialogue",
        "seed": 101,
        "prompt": (
            "Two coworkers at a rainy bus stop argue about being late; include clear spoken "
            "English dialogue with visible lip-sync, rain, traffic, and street ambience."
        ),
    },
    {
        "id": "s02_multilingual",
        "category": "multilingual_dialogue",
        "seed": 202,
        "prompt": (
            "In a Tokyo ramen shop, the chef calls orders in Japanese and a tourist replies in "
            "English; both languages must be audible and lip-synced over kitchen sounds."
        ),
    },
    {
        "id": "s03_wetland",
        "category": "natural_ambience",
        "seed": 303,
        "prompt": (
            "A pre-dawn wetland wakes beneath distant lightning; layer birds, insects, thunder, "
            "water, and wind through reeds with no dialogue and rich natural audio throughout."
        ),
    },
    {
        "id": "s04_cyclist",
        "category": "score_and_ambience",
        "seed": 404,
        "prompt": (
            "A lone cyclist rides an empty neon highway at night; use a cinematic orchestral "
            "score together with audible tire hum, chain clicks, breathing, and wind."
        ),
    },
    {
        "id": "s05_wok",
        "category": "action_sync",
        "seed": 505,
        "prompt": (
            "A chef flips a sizzling wok, tosses noodles high, and catches them; synchronize every "
            "motion with roaring flame, sizzling oil, metal clangs, and spatula hits."
        ),
    },
    {
        "id": "s06_sneaker",
        "category": "timed_cuts",
        "seed": 606,
        "prompt": (
            "A fifteen-second sneaker advertisement moves from a wide city sprint to a side "
            "tracking shot and then a sole macro, with rhythmic footfalls and transition whooshes."
        ),
    },
    {
        "id": "s07_bowling",
        "category": "physics_and_impact",
        "seed": 707,
        "prompt": (
            "In a bowling alley a spinning ball rolls down the lane and strikes the pins; show "
            "realistic momentum and pin scatter with rolling rumble and a loud synchronized crash."
        ),
    },
    {
        "id": "s08_jazz",
        "category": "diegetic_music",
        "seed": 808,
        "prompt": (
            "A street jazz trio of saxophone, upright bass, and brush drums performs in a plaza "
            "while passersby clap; the live in-scene music and crowd reactions must be audible."
        ),
    },
    {
        "id": "s09_noir",
        "category": "voiceover",
        "seed": 909,
        "prompt": (
            "A film-noir detective walks through neon rain while a calm male off-screen voiceover "
            "narrates the case; her lips remain closed beneath rain and distant sirens."
        ),
    },
    {
        "id": "s10_phone_call",
        "category": "cross_cut_audio",
        "seed": 1010,
        "prompt": (
            "A phone call alternates between a quiet office and a busy café; the same English "
            "conversation continues seamlessly across two cuts with uninterrupted synchronized audio."
        ),
    },
    # --- camera / cut stress set (s11+) ---
    {
        "id": "s11_museum_reveal",
        "category": "pedestal_push_cut",
        "seed": 1111,
        "prompt": (
            "In a dark museum hall, start low on a marble floor, pedestal up to reveal a glowing "
            "statue, then slowly push in; around mid-clip hard-cut to a tight detail of the statue's "
            "cracked face as footsteps echo and a soft string score swells. No dialogue."
        ),
    },
    {
        "id": "s12_alley_chase",
        "category": "tracking_shake_cuts",
        "seed": 1212,
        "prompt": (
            "A nighttime alley chase: a handheld tracking shot follows a runner from behind with "
            "strong camera shake, then whip-cut to a side trucking shot, then cut to a frontal "
            "close-up as they gasp English dialogue while sprinting; keep footfalls, panting, "
            "clattering trash cans, and distant sirens continuous across cuts."
        ),
    },
    {
        "id": "s13_rooftop_orbit",
        "category": "arc_shot_dialogue",
        "seed": 1313,
        "prompt": (
            "On a windy rooftop at golden hour, the camera arcs 180 degrees around a couple; the "
            "man proposes in clear English with lip-sync, then cut to her close-up reaction as she "
            "answers; wind, city hum, and a quiet piano underscore remain audible."
        ),
    },
    {
        "id": "s14_kitchen_stations",
        "category": "whip_pan_montage",
        "seed": 1414,
        "prompt": (
            "A busy restaurant kitchen montage: open on a wide shot, fast whip-pan to the grill, "
            "hard-cut to a plating close-up, then pull out to the pass window as the chef shouts a "
            "short English order; sync sizzles, knife chops, ticket printer, and plate clinks to "
            "each cut."
        ),
    },
    {
        "id": "s15_concert_crashzoom",
        "category": "crash_zoom_multicut",
        "seed": 1515,
        "prompt": (
            "A live arena concert with four timed cuts in 15 seconds: wide crowd, crash zoom onto "
            "the lead singer mid-lyric in English, cut to drummer close-up, then pull out to a "
            "stage-wide finale; diegetic band performance, crowd roar, and stage whooshes must "
            "stay continuous."
        ),
    },
    {
        "id": "s16_train_matchcut",
        "category": "pov_matchcut_carryover",
        "seed": 1616,
        "prompt": (
            "Start as a train-window POV rushing into a dark tunnel, then match-cut to the same "
            "passenger in a medium shot as daylight returns; one continuous English line of dialogue "
            "must carry seamlessly across the cut while rail clatter morphs with the lighting change."
        ),
    },
]


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def prepare() -> None:
    for directory in (
        "prompts/raw",
        "prompts/requests",
        "pe",
        "jobs",
        "videos/raw",
        "videos/pe",
        "eval",
    ):
        (ROOT / directory).mkdir(parents=True, exist_ok=True)
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT.parents[1],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    dump(
        ROOT / "experiment.json",
        {
            "experiment_id": ROOT.name,
            "created_unix": int(time.time()),
            "omni_rewriter_revision": revision,
            "task": "t2va",
            "duration_seconds": DURATION,
            "target": TARGET,
            "writer_model": "Qwen3.5-122B-A10B",
            "h3_model": "/pfs/weiyang/MiniMax-H3",
            "scenario_count": len(SCENARIOS),
            "arms": ["raw", "pe"],
        },
    )
    for scene in SCENARIOS:
        request = {
            "prompt": scene["prompt"],
            "duration_seconds": DURATION,
            "task": "t2va",
            "metadata": {"aspect_ratio": "16:9", "seed": str(scene["seed"])},
        }
        dump(ROOT / "prompts" / "raw" / f"{scene['id']}.json", scene)
        dump(ROOT / "prompts" / "requests" / f"{scene['id']}.json", request)
    build_compare_site()
    print(f"Prepared {len(SCENARIOS)} scenarios in {ROOT}")


def build_compare_site() -> None:
    """Regenerate intranet compare UI with RAW prompts labeled (no stitched videos)."""
    nav = "".join(
        f'<a href="#{html.escape(scene["id"])}">{html.escape(scene["id"])}</a>'
        for scene in SCENARIOS
    )
    cards: list[str] = []
    for scene in SCENARIOS:
        sid = html.escape(scene["id"])
        cat = html.escape(scene["category"])
        prompt = html.escape(scene["prompt"])
        seed = scene["seed"]
        cards.append(
            f"""
    <section class="card" id="{sid}">
      <header>
        <h2>{sid} <span class="cat">{cat}</span></h2>
        <p class="raw-prompt"><strong>RAW prompt</strong> {prompt}</p>
      </header>
      <div class="pair">
        <figure>
          <figcaption>RAW <small>seed={seed}</small></figcaption>
          <video controls preload="metadata" src="/videos/raw/{sid}.mp4"></video>
        </figure>
        <figure>
          <figcaption>PE Omni-Rewriter <small>seed={seed}</small></figcaption>
          <video controls preload="metadata" src="/videos/pe/{sid}.mp4"></video>
        </figure>
      </div>
      <details>
        <summary>Show PE H3 prompt</summary>
        <pre class="pe-text" data-src="/pe/{sid}.h3.txt">loading…</pre>
      </details>
    </section>"""
        )
    page = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Omni-Rewriter PE vs RAW · MiniMax-H3 15s</title>
<style>
:root {{
  --bg:#0f1419; --panel:#1a222c; --text:#e8eef5; --muted:#9aa7b5; --accent:#5eb1ff; --line:#2a3542;
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0; font-family:"IBM Plex Sans","Noto Sans SC",system-ui,sans-serif;
  background:radial-gradient(1200px 600px at 10% -10%, #1c2a3a, transparent),
             radial-gradient(900px 500px at 100% 0%, #1a2430, transparent), var(--bg);
  color:var(--text); line-height:1.45;
}}
header.top {{
  position:sticky; top:0; z-index:10; backdrop-filter:blur(10px);
  background:rgba(15,20,25,.88); border-bottom:1px solid var(--line);
  padding:14px 24px; display:flex; gap:16px; align-items:baseline; flex-wrap:wrap;
}}
header.top h1 {{ margin:0; font-size:1.15rem; letter-spacing:.02em; }}
header.top p {{ margin:0; color:var(--muted); font-size:.92rem; }}
nav {{ display:flex; flex-wrap:wrap; gap:8px; padding:12px 24px 0; }}
nav a {{
  color:var(--muted); text-decoration:none; border:1px solid var(--line);
  border-radius:999px; padding:4px 10px; font-size:.8rem;
}}
nav a:hover {{ color:var(--text); border-color:var(--accent); }}
main {{ max-width:1500px; margin:0 auto; padding:8px 24px 48px; }}
.card {{
  margin:22px 0; padding:18px; background:var(--panel); border:1px solid var(--line);
  border-radius:14px;
}}
.card h2 {{ margin:0 0 8px; font-size:1.05rem; }}
.cat {{ color:var(--accent); font-weight:500; font-size:.85rem; margin-left:8px; }}
.raw-prompt {{
  margin:0 0 14px; padding:12px 14px; background:#12181f; border-left:3px solid var(--accent);
  border-radius:8px; color:#d7e2ec;
}}
.pair {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
@media (max-width:900px) {{ .pair {{ grid-template-columns:1fr; }} }}
figure {{ margin:0; }}
figcaption {{ font-size:.85rem; color:var(--muted); margin-bottom:6px; }}
video {{ width:100%; background:#000; border-radius:10px; aspect-ratio:16/9; }}
details {{ margin-top:12px; }}
summary {{ cursor:pointer; color:var(--accent); }}
pre.pe-text {{
  white-space:pre-wrap; word-break:break-word; background:#0c1116; padding:12px;
  border-radius:8px; font-size:.82rem; color:#c9d4df; max-height:320px; overflow:auto;
}}
.toolbar {{ display:flex; gap:10px; flex-wrap:wrap; margin:8px 24px; }}
button {{
  background:#243040; color:var(--text); border:1px solid var(--line); border-radius:8px;
  padding:8px 12px; cursor:pointer;
}}
button:hover {{ border-color:var(--accent); }}
</style>
</head>
<body>
<header class="top">
  <h1>Omni-Rewriter · RAW vs PE</h1>
  <p>MiniMax-H3 Base T2VA · 15s · 768p · {len(SCENARIOS)} scenes · same seed per scene · audio enabled</p>
</header>
<div class="toolbar">
  <button type="button" id="syncPlay">同步播放当前页视频</button>
  <button type="button" id="pauseAll">全部暂停</button>
</div>
<nav>
{nav}
</nav>
<main>
{"".join(cards)}
</main>
<script>
document.querySelectorAll('pre.pe-text[data-src]').forEach(async (el) => {{
  try {{
    const r = await fetch(el.dataset.src);
    el.textContent = r.ok ? await r.text() : '(PE prompt not generated yet)';
  }} catch (e) {{
    el.textContent = '(failed to load PE prompt)';
  }}
}});
document.getElementById('syncPlay').onclick = () => {{
  document.querySelectorAll('video').forEach(v => {{ v.currentTime = 0; v.play(); }});
}};
document.getElementById('pauseAll').onclick = () => {{
  document.querySelectorAll('video').forEach(v => v.pause());
}};
</script>
</body>
</html>
"""
    web_dir = ROOT / "web"
    web_dir.mkdir(parents=True, exist_ok=True)
    (web_dir / "index.html").write_text(page, encoding="utf-8")
    (ROOT / "index.html").write_text(
        '<!doctype html><meta http-equiv="refresh" content="0; url=/web/index.html">'
        '<a href="/web/index.html">Open comparison</a>\n',
        encoding="utf-8",
    )
    print(f"Wrote compare site for {len(SCENARIOS)} scenes -> {web_dir / 'index.html'}")


async def expand_all(base_url: str, model: str) -> None:
    config = ChatBackendConfig(
        base_url=base_url,
        model=model,
        timeout=600,
        retries=2,
        temperature=0.2,
        max_tokens=8192,
        enable_thinking=False,
    )
    backend = OpenAICompatibleBackend(config)
    media = MediaPreparer()
    agent = RewriteAgent(
        backend,
        media_preparer=media,
        config=RewriteAgentConfig(max_repairs=3, trace_path=ROOT / "pe" / "trace.jsonl"),
    )
    manifest: list[dict[str, Any]] = []
    try:
        for index, scene in enumerate(SCENARIOS, start=1):
            request_path = ROOT / "prompts" / "requests" / f"{scene['id']}.json"
            request = RewriteRequest.model_validate(load(request_path))
            print(f"[{index}/{len(SCENARIOS)}] Expanding {scene['id']}...", flush=True)
            result = await agent.run(request)
            h3_text = result.output.render()
            expanded = {
                "scenario_id": scene["id"],
                "output": result.output.model_dump(mode="json"),
                "analysis": result.analysis.model_dump(mode="json"),
                "repairs": result.repairs,
                "run_id": result.run_id,
                "h3_text": h3_text,
            }
            dump(ROOT / "pe" / f"{scene['id']}.expand.json", expanded)
            (ROOT / "pe" / f"{scene['id']}.h3.txt").write_text(
                h3_text + "\n", encoding="utf-8"
            )
            manifest.append(
                {
                    "scenario_id": scene["id"],
                    "category": scene["category"],
                    "seed": scene["seed"],
                    "request": request.model_dump(mode="json"),
                    "arms": {
                        "raw": {"prompt": scene["prompt"]},
                        "pe": {"prompt": h3_text, "repairs": result.repairs},
                    },
                    "videos": {
                        "raw": f"videos/raw/{scene['id']}.mp4",
                        "pe": f"videos/pe/{scene['id']}.mp4",
                    },
                }
            )
    finally:
        await backend.aclose()
        await media.aclose()
    (ROOT / "manifest.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in manifest),
        encoding="utf-8",
    )
    print("All PE prompts validated and saved.")


async def h3_request(client: httpx.AsyncClient, method: str, path: str, **kwargs: Any) -> Any:
    response = await client.request(method, path, **kwargs)
    response.raise_for_status()
    if "application/json" in response.headers.get("content-type", ""):
        return response.json()
    return response.content


async def wait_for_job(client: httpx.AsyncClient, job_id: str) -> dict[str, Any]:
    while True:
        status = await h3_request(client, "GET", f"/v1/videos/{job_id}")
        state = str(status.get("status", "")).lower()
        if state in {"completed", "succeeded", "success", "done"}:
            return status
        if state in {"failed", "error", "cancelled", "canceled"}:
            raise RuntimeError(f"H3 job {job_id} failed: {status}")
        print(f"  job={job_id} status={state or 'unknown'}", flush=True)
        await asyncio.sleep(10)


async def generate_all(
    base_url: str,
    *,
    arms: tuple[str, ...] = ("raw", "pe"),
    force: bool = False,
) -> None:
    manifest = [
        json.loads(line)
        for line in (ROOT / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    total = len(manifest)
    async with httpx.AsyncClient(base_url=base_url, timeout=1800) as client:
        for scene_index, item in enumerate(manifest, start=1):
            for arm in arms:
                destination = ROOT / item["videos"][arm]
                if (
                    not force
                    and destination.exists()
                    and destination.stat().st_size > 0
                ):
                    print(
                        f"[{scene_index}/{total} {arm}] exists, skipping {destination.name}"
                    )
                    continue
                payload = {
                    "task": "t2va",
                    "prompt": item["arms"][arm]["prompt"],
                    "conditions": [],
                    "target": TARGET,
                    "seed": item["seed"],
                }
                print(
                    f"[{scene_index}/{total} {arm}] submitting "
                    f"{item['scenario_id']} seed={item['seed']}",
                    flush=True,
                )
                submitted = await h3_request(client, "POST", "/v1/videos", json=payload)
                job_id = str(submitted["id"])
                dump(
                    ROOT / "jobs" / f"{item['scenario_id']}.{arm}.json",
                    {"id": job_id, "payload": payload, "submitted": submitted},
                )
                final = await wait_for_job(client, job_id)
                content = await h3_request(client, "GET", f"/v1/videos/{job_id}/content")
                if not isinstance(content, bytes):
                    raise TypeError(f"H3 content for {job_id} was not binary")
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)
                dump(
                    ROOT / "jobs" / f"{item['scenario_id']}.{arm}.final.json",
                    final,
                )
                print(f"  saved {destination} ({len(content)} bytes)", flush=True)


def probe(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size:stream=index,codec_type,codec_name,sample_rate,channels,width,height",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    stream_types = {stream["codec_type"] for stream in data.get("streams", [])}
    data["valid_audio_video"] = {"audio", "video"} <= stream_types
    return data


def verify() -> None:
    results: list[dict[str, Any]] = []
    rows: list[str] = []
    for scene in SCENARIOS:
        entry: dict[str, Any] = {"scenario_id": scene["id"], "arms": {}}
        for arm in ("raw", "pe"):
            path = ROOT / "videos" / arm / f"{scene['id']}.mp4"
            if not path.exists():
                entry["arms"][arm] = {"exists": False}
                continue
            details = probe(path)
            entry["arms"][arm] = {"exists": True, "probe": details}
            if not details["valid_audio_video"]:
                raise RuntimeError(f"{path} does not contain both audio and video")
        results.append(entry)
        rows.append(
            f"""<section><h2>{scene['id']} — {scene['category']}</h2>
<p>{scene['prompt']}</p><div class="pair">
<figure><figcaption>Raw prompt</figcaption><video controls preload="metadata"
src="videos/raw/{scene['id']}.mp4"></video></figure>
<figure><figcaption>Omni-Rewriter PE</figcaption><video controls preload="metadata"
src="videos/pe/{scene['id']}.mp4"></video></figure></div></section>"""
        )
    dump(ROOT / "eval" / "media_probe.json", results)
    html = """<!doctype html><meta charset="utf-8"><title>Raw vs PE</title>
<style>body{font-family:sans-serif;max-width:1500px;margin:auto}.pair{display:flex;gap:16px}
figure{flex:1;margin:0}video{width:100%}section{border-bottom:1px solid #ccc;padding:16px}</style>
<h1>MiniMax-H3 Base 15s: Raw prompt vs Omni-Rewriter PE</h1>""" + "\n".join(rows)
    (ROOT / "comparison.html").write_text(html, encoding="utf-8")
    valid = sum(
        bool(entry["arms"].get(arm, {}).get("probe", {}).get("valid_audio_video"))
        for entry in results
        for arm in ("raw", "pe")
    )
    expected = len(SCENARIOS) * 2
    print(
        f"Verified {valid}/{expected} files with both audio and video; "
        f"open {ROOT / 'comparison.html'}"
    )
    build_compare_site()


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("prepare")
    expand_parser = subparsers.add_parser("expand")
    expand_parser.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    expand_parser.add_argument("--model", default="Qwen3.5-122B-A10B")
    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("--base-url", default="http://127.0.0.1:30010")
    generate_parser.add_argument(
        "--arms",
        default="raw,pe",
        help="Comma-separated arms to generate, e.g. pe or raw,pe",
    )
    generate_parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even when output videos already exist",
    )
    subparsers.add_parser("verify")
    subparsers.add_parser("build-web")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "expand":
        asyncio.run(expand_all(args.base_url, args.model))
    elif args.command == "generate":
        arms = tuple(part.strip() for part in args.arms.split(",") if part.strip())
        asyncio.run(generate_all(args.base_url, arms=arms, force=args.force))
    elif args.command == "build-web":
        build_compare_site()
    else:
        verify()


if __name__ == "__main__":
    main()
