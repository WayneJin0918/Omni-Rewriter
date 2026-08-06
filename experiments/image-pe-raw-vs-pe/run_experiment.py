#!/usr/bin/env python3
"""Image PE raw-vs-expanded comparison (Seedream + Qwen-Image-Edit dialects)."""

from __future__ import annotations

import argparse
import asyncio
import html
import json
import time
from pathlib import Path
from typing import Any

from omni_rewriter.agent import RewriteAgent, RewriteAgentConfig
from omni_rewriter.backends import ChatBackendConfig, OpenAICompatibleBackend
from omni_rewriter.media_input import MediaPreparer
from omni_rewriter.models import ImageRewrite, RewriteRequest
from omni_rewriter.service import validate_output

ROOT = Path(__file__).resolve().parent

SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "i01_neon_poster",
        "category": "seedream_t2i",
        "profile": "seedream",
        "task": "t2i",
        "prompt": "做一张横版海报，主标题写“夏日限定”，霓虹寿司店门口，雨夜反光地面，要有电影感",
    },
    {
        "id": "i02_product_square",
        "category": "seedream_t2i",
        "profile": "seedream",
        "task": "t2i",
        "prompt": "Square product shot of a matte black wireless earbud case with the logo text Hello printed cleanly on the lid, soft studio light",
    },
    {
        "id": "i03_ultrawide_banner",
        "category": "seedream_t2i",
        "profile": "seedream",
        "task": "t2i",
        "prompt": "Ultra-wide website hero of a desert highway at dusk with a single classic convertible, no people, cinematic dust",
    },
    {
        "id": "i04_phone_wallpaper",
        "category": "seedream_t2i",
        "profile": "seedream",
        "task": "t2i",
        "prompt": "竖版手机壁纸：竹林雾气，一只白鹤站在石头上，底部小字“清心”",
    },
    {
        "id": "i05_latex_board",
        "category": "seedream_t2i",
        "profile": "seedream",
        "task": "t2i",
        "prompt": "A classroom blackboard clearly showing the formula E=mc^2 written in chalk, empty desks in front, soft daylight",
    },
    {
        "id": "i06_edit_dress",
        "category": "qwen_image_edit",
        "profile": "qwen_image_edit",
        "task": "image_edit",
        "prompt": "Keep the woman and pose from the reference, change her dress to red velvet, keep the background",
        "needs_media": True,
    },
    {
        "id": "i07_edit_bg_swap",
        "category": "qwen_image_edit",
        "profile": "qwen_image_edit",
        "task": "image_edit",
        "prompt": "保留人物五官与发型，把背景换成雨夜东京街景，地面要有霓虹倒影",
        "needs_media": True,
    },
    {
        "id": "i08_i2i_style_merge",
        "category": "seedream_i2i",
        "profile": "seedream",
        "task": "i2i",
        "prompt": "Combine the subject from image 1 with the watercolor style of image 2, keep identity, soft paper texture",
        "needs_media": True,
        "media_count": 2,
    },
]

# Curated PE gold used when the writer backend is offline (still schema-valid).
GOLD_PE: dict[str, dict[str, Any]] = {
    "i01_neon_poster": {
        "task": "t2i",
        "profile": "seedream",
        "prompt": (
            "A cinematic rainy night storefront of a neon sushi shop, wet asphalt reflecting pink "
            "and cyan neon, a horizontal poster composition with the on-sign title “夏日限定” in "
            "clear glowing characters above the entrance, shallow puddles, steam from a sidewalk "
            "vent, no people in the foreground."
        ),
        "ratio": "16:9",
    },
    "i02_product_square": {
        "task": "t2i",
        "profile": "seedream",
        "prompt": (
            "A square studio product photograph of a matte black wireless earbud charging case "
            "centered on a seamless light-gray sweep, soft boxed key light with gentle rim "
            "separation, the lid printed with the exact logo text \"Hello\", clean reflections, "
            "no extra props."
        ),
        "ratio": "1:1",
    },
    "i03_ultrawide_banner": {
        "task": "t2i",
        "profile": "seedream",
        "prompt": (
            "An ultra-wide dusk desert highway receding to the horizon, a single classic "
            "convertible parked on the shoulder, low sun backlighting airborne dust, long "
            "asphalt leading lines, empty of people, cinematic still suitable for a website hero."
        ),
        "ratio": "21:9",
    },
    "i04_phone_wallpaper": {
        "task": "t2i",
        "profile": "seedream",
        "prompt": (
            "A tall misty bamboo forest with layered trunks fading into fog, a white crane "
            "standing on a dark wet stone in the lower third, soft diffused daylight, and small "
            "on-image calligraphy text “清心” near the bottom edge."
        ),
        "ratio": "9:16",
    },
    "i05_latex_board": {
        "task": "t2i",
        "profile": "seedream",
        "prompt": (
            "A classroom blackboard filling most of the frame with chalk writing that clearly "
            "shows \"E=mc^2\", empty wooden desks in soft focus in the foreground, cool daylight "
            "from a side window, dust motes in the air, documentary still."
        ),
        "ratio": "4:3",
    },
    "i06_edit_dress": {
        "task": "image_edit",
        "profile": "qwen_image_edit",
        "prompt": (
            "Keep the woman, face, hair, and pose from image 1 unchanged; replace only her dress "
            "with a red velvet dress of similar silhouette; preserve the original background, "
            "lighting direction, and camera framing."
        ),
        "ratio": "[image 1]",
    },
    "i07_edit_bg_swap": {
        "task": "image_edit",
        "profile": "qwen_image_edit",
        "prompt": (
            "保留 image 1 中人物的五官、发型与表情不变，仅将背景替换为雨夜东京街景，地面需有清晰霓虹倒影，"
            "人物边缘光照与新环境一致，不改变人物比例与构图。"
        ),
        "ratio": "[image 1]",
    },
    "i08_i2i_style_merge": {
        "task": "i2i",
        "profile": "seedream",
        "prompt": (
            "Preserve the subject identity and pose from image 1 while restyling the entire frame "
            "into the watercolor look of image 2, soft paper tooth, translucent pigment edges, "
            "and gentle bleeding of washes without changing facial structure."
        ),
        "ratio": "[image 1]",
    },
}


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _request_for(scene: dict[str, Any]) -> dict[str, Any]:
    media = []
    if scene.get("needs_media"):
        count = int(scene.get("media_count", 1))
        for index in range(1, count + 1):
            media.append(
                {
                    "media_type": "image",
                    "role": "reference",
                    "uri": f"file:///tmp/omni_rewriter_placeholder_{scene['id']}_{index}.png",
                    "name": f"image {index}",
                }
            )
    return {
        "prompt": scene["prompt"],
        "task": scene["task"],
        "media": media,
        "metadata": {"image_pe_profile": scene["profile"]},
    }


def prepare() -> None:
    dump(
        ROOT / "experiment.json",
        {
            "experiment_id": ROOT.name,
            "created_unix": int(time.time()),
            "modality": "image",
            "profiles": ["seedream", "qwen_image_edit"],
            "scenario_count": len(SCENARIOS),
            "arms": ["raw", "pe"],
        },
    )
    for scene in SCENARIOS:
        dump(ROOT / "prompts" / "raw" / f"{scene['id']}.json", scene)
        dump(ROOT / "prompts" / "requests" / f"{scene['id']}.json", _request_for(scene))
        gold = GOLD_PE[scene["id"]]
        ImageRewrite.model_validate(gold)
        dump(ROOT / "pe" / f"{scene['id']}.expand.json", {"scenario_id": scene["id"], "output": gold, "source": "gold"})
        rendered = ImageRewrite.model_validate(gold).render()
        (ROOT / "pe" / f"{scene['id']}.txt").write_text(rendered + "\n", encoding="utf-8")
    build_compare_site()
    print(f"Prepared {len(SCENARIOS)} image PE scenarios in {ROOT}")


async def expand_all(base_url: str, model: str) -> None:
    backend = OpenAICompatibleBackend(
        ChatBackendConfig(
            base_url=base_url,
            model=model,
            timeout=600,
            retries=2,
            temperature=0.2,
            max_tokens=4096,
            enable_thinking=False,
        )
    )
    media = MediaPreparer()
    agent = RewriteAgent(
        backend,
        media_preparer=media,
        config=RewriteAgentConfig(max_repairs=3, trace_path=ROOT / "pe" / "trace.jsonl"),
    )
    try:
        for index, scene in enumerate(SCENARIOS, start=1):
            if scene.get("needs_media"):
                print(
                    f"[{index}/{len(SCENARIOS)}] skip live expand for {scene['id']} "
                    "(placeholder media; using gold until real refs are attached)",
                    flush=True,
                )
                continue
            request = RewriteRequest.model_validate(
                json.loads((ROOT / "prompts" / "requests" / f"{scene['id']}.json").read_text())
            )
            print(f"[{index}/{len(SCENARIOS)}] Expanding {scene['id']}...", flush=True)
            result = await agent.run(request)
            assert isinstance(result.output, ImageRewrite)
            dump(
                ROOT / "pe" / f"{scene['id']}.expand.json",
                {
                    "scenario_id": scene["id"],
                    "output": result.output.model_dump(mode="json"),
                    "analysis": result.analysis.model_dump(mode="json"),
                    "repairs": result.repairs,
                    "run_id": result.run_id,
                    "source": "writer",
                },
            )
            (ROOT / "pe" / f"{scene['id']}.txt").write_text(
                result.output.render() + "\n", encoding="utf-8"
            )
    finally:
        await backend.aclose()
        await media.aclose()
    build_compare_site()
    print("Image PE expand complete.")


def build_compare_site() -> None:
    nav = "".join(f'<a href="#{html.escape(s["id"])}">{html.escape(s["id"])}</a>' for s in SCENARIOS)
    cards: list[str] = []
    for scene in SCENARIOS:
        sid = scene["id"]
        pe_path = ROOT / "pe" / f"{sid}.txt"
        pe_json = ROOT / "pe" / f"{sid}.expand.json"
        pe_text = pe_path.read_text(encoding="utf-8") if pe_path.exists() else "(missing)"
        ratio = ""
        profile = scene["profile"]
        if pe_json.exists():
            data = json.loads(pe_json.read_text(encoding="utf-8"))
            ratio = data.get("output", {}).get("ratio", "")
            profile = data.get("output", {}).get("profile", profile)
        cards.append(
            f"""
<section class="card" id="{html.escape(sid)}">
  <header>
    <h2>{html.escape(sid)} <span class="cat">{html.escape(scene['category'])}</span></h2>
    <p class="meta">task=<code>{html.escape(scene['task'])}</code> · profile=<code>{html.escape(profile)}</code> · ratio=<code>{html.escape(str(ratio))}</code></p>
    <p class="raw-prompt"><strong>RAW</strong> {html.escape(scene['prompt'])}</p>
  </header>
  <div class="pair">
    <figure>
      <figcaption>RAW intent</figcaption>
      <pre>{html.escape(scene['prompt'])}</pre>
    </figure>
    <figure>
      <figcaption>PE Omni-Rewriter</figcaption>
      <pre>{html.escape(pe_text)}</pre>
    </figure>
  </div>
</section>"""
        )
    page = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Omni-Rewriter Image PE · RAW vs Expanded</title>
<style>
:root {{ --bg:#10141a; --panel:#1a222c; --text:#e8eef5; --muted:#9aa7b5; --accent:#6bcf8e; --line:#2a3542; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:"IBM Plex Sans","Noto Sans SC",system-ui,sans-serif; background:var(--bg); color:var(--text); }}
header.top {{ position:sticky; top:0; background:rgba(16,20,26,.92); border-bottom:1px solid var(--line); padding:14px 24px; }}
header.top h1 {{ margin:0; font-size:1.1rem; }}
header.top p {{ margin:4px 0 0; color:var(--muted); font-size:.9rem; }}
nav {{ display:flex; flex-wrap:wrap; gap:8px; padding:12px 24px 0; }}
nav a {{ color:var(--muted); text-decoration:none; border:1px solid var(--line); border-radius:999px; padding:4px 10px; font-size:.8rem; }}
main {{ max-width:1400px; margin:0 auto; padding:8px 24px 48px; }}
.card {{ margin:20px 0; padding:16px; background:var(--panel); border:1px solid var(--line); border-radius:12px; }}
.cat {{ color:var(--accent); font-size:.85rem; margin-left:8px; }}
.meta {{ color:var(--muted); font-size:.85rem; }}
.raw-prompt {{ background:#12181f; border-left:3px solid var(--accent); padding:10px 12px; border-radius:8px; }}
.pair {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
@media (max-width:900px) {{ .pair {{ grid-template-columns:1fr; }} }}
figcaption {{ color:var(--muted); margin-bottom:6px; font-size:.85rem; }}
pre {{ white-space:pre-wrap; word-break:break-word; background:#0c1116; padding:12px; border-radius:8px; min-height:120px; font-size:.86rem; }}
</style>
</head>
<body>
<header class="top">
  <h1>Omni-Rewriter · Image PE</h1>
  <p>Seedream + Qwen-Image-Edit dialects · RAW intent vs expanded blueprint · {len(SCENARIOS)} cases</p>
</header>
<nav>{nav}</nav>
<main>{''.join(cards)}</main>
</body>
</html>
"""
    (ROOT / "web" / "index.html").write_text(page, encoding="utf-8")
    (ROOT / "index.html").write_text(
        '<!doctype html><meta http-equiv="refresh" content="0; url=/web/index.html">'
        '<a href="/web/index.html">Open image PE comparison</a>\n',
        encoding="utf-8",
    )
    print(f"Wrote {ROOT / 'web' / 'index.html'}")


def validate_gold() -> None:
    for scene in SCENARIOS:
        path = ROOT / "pe" / f"{scene['id']}.expand.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        validate_output({"request": _request_for(scene), "output": data["output"]})
    print(f"Validated {len(SCENARIOS)} image PE envelopes")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    expand_p = sub.add_parser("expand")
    expand_p.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    expand_p.add_argument("--model", default="Qwen3.5-122B-A10B")
    sub.add_parser("build-web")
    sub.add_parser("validate")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "expand":
        asyncio.run(expand_all(args.base_url, args.model))
    elif args.command == "build-web":
        build_compare_site()
    else:
        validate_gold()


if __name__ == "__main__":
    main()
