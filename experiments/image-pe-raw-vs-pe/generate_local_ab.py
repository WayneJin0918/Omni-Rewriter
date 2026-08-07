#!/usr/bin/env python3
"""Generate reproducible local RAW-vs-PE image examples.

Heavy model imports are intentionally local to each backend function so the
experiment metadata and gallery builder remain usable without GPU dependencies.
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"
GALLERY = Path(__file__).resolve().parents[2] / "docs" / "assets" / "gallery" / "image"

QWEN_T2I = Path("/pfs/weiyang/WISE_re/CKPT/Qwen/Qwen-Image-2512")
QWEN_EDIT = Path("/pfs/weiyang/WISE_re/CKPT/Qwen/Qwen-Image-Edit-2511")
HUNYUAN = Path("/pfs/weiyang/WISE_re/CKPT/tencent/HunyuanImage-3.0")
HUNYUAN_SOURCE = Path("/pfs/weiyang/WISE_re/HunyuanImage-3.0")

SEED = 20260806
QWEN_STEPS = 30
QWEN_WIDTH = 1024
QWEN_HEIGHT = 576
EDIT_SIZE = 768

T2I_RAW = (
    "做一张横版海报，主标题写“夏日限定”，霓虹寿司店门口，"
    "雨夜反光地面，要有电影感"
)
T2I_PE = (
    "A cinematic rainy night storefront of a neon sushi shop, wet asphalt reflecting "
    "pink and cyan neon, a horizontal poster composition with the on-sign title “夏日限定” "
    "in clear glowing characters above the entrance, shallow puddles, steam from a sidewalk "
    "vent, no people in the foreground."
)
REFERENCE_PROMPT = (
    "A realistic waist-up studio portrait of an East Asian woman in her late twenties, "
    "shoulder-length black hair, neutral expression, standing front-facing in a plain white "
    "cotton dress against a light gray seamless background, soft even daylight, centered framing."
)
EDIT_RAW = "把她的白色裙子换成红色丝绒裙，其他都不变"
EDIT_PE = (
    "Keep the woman, face, shoulder-length black hair, expression, pose, body proportions, "
    "camera framing, gray studio background, and lighting from image 1 unchanged; replace only "
    "the white cotton dress with a deep red velvet dress of the same silhouette, with visible "
    "soft pile texture and physically consistent folds and highlights."
)
HUNYUAN_RAW = "一张未来感城市图书馆的横版概念图，中央写“知识之光”"
HUNYUAN_PE = (
    "A wide architectural concept image of a near-future public library at blue hour, a glass "
    "and pale-stone facade centered behind a broad pedestrian plaza, warm interior reading rooms "
    "visible through the glazing, restrained cyan wayfinding lights, small groups of visitors "
    "providing scale, and the exact illuminated entrance text “知识之光”, balanced 16:9 composition."
)


def _save_manifest(backend: str, records: list[dict[str, Any]]) -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    payload = {
        "backend": backend,
        "created_unix": int(time.time()),
        "host": platform.node(),
        "seed": SEED,
        "records": records,
        "git_revision": subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT.parents[1],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip(),
    }
    (OUTPUTS / f"{backend}.manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _gallery_copy(source: Path, name: str) -> None:
    from PIL import Image

    GALLERY.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        image.thumbnail((768, 768))
        image.convert("RGB").save(GALLERY / f"{name}.webp", "WEBP", quality=72, method=6)


def qwen_t2i() -> None:
    import torch
    from diffusers import DiffusionPipeline

    destination = OUTPUTS / "qwen_image_2512"
    destination.mkdir(parents=True, exist_ok=True)
    pipe = DiffusionPipeline.from_pretrained(QWEN_T2I, torch_dtype=torch.bfloat16).to("cuda")
    common = {
        "negative_prompt": (
            "低分辨率，低画质，肢体畸形，画面过饱和，文字模糊，扭曲，构图混乱。"
        ),
        "width": QWEN_WIDTH,
        "height": QWEN_HEIGHT,
        "num_inference_steps": QWEN_STEPS,
        "true_cfg_scale": 4.0,
    }
    records = []
    for arm, prompt in (("raw", T2I_RAW), ("pe", T2I_PE)):
        generator = torch.Generator(device="cuda").manual_seed(SEED)
        image = pipe(prompt=prompt, generator=generator, **common).images[0]
        path = destination / f"{arm}.png"
        image.save(path)
        _gallery_copy(path, f"qwen_t2i_{arm}")
        records.append(
            {
                "arm": arm,
                "prompt": prompt,
                "path": str(path.relative_to(ROOT)),
                **common,
            }
        )
    _save_manifest("qwen_image_2512", records)
    del pipe
    gc.collect()
    torch.cuda.empty_cache()


def qwen_edit() -> None:
    import torch
    from diffusers import DiffusionPipeline, QwenImageEditPlusPipeline

    destination = OUTPUTS / "qwen_image_edit_2511"
    destination.mkdir(parents=True, exist_ok=True)
    reference_path = destination / "reference.png"
    if not reference_path.exists():
        reference_pipe = DiffusionPipeline.from_pretrained(
            QWEN_T2I, torch_dtype=torch.bfloat16
        ).to("cuda")
        reference = reference_pipe(
            prompt=REFERENCE_PROMPT,
            width=EDIT_SIZE,
            height=EDIT_SIZE,
            num_inference_steps=QWEN_STEPS,
            true_cfg_scale=4.0,
            generator=torch.Generator(device="cuda").manual_seed(SEED + 1),
        ).images[0]
        reference.save(reference_path)
        del reference_pipe
        gc.collect()
        torch.cuda.empty_cache()

    from PIL import Image

    reference = Image.open(reference_path).convert("RGB")
    pipe = QwenImageEditPlusPipeline.from_pretrained(
        QWEN_EDIT, torch_dtype=torch.bfloat16
    ).to("cuda")
    common = {
        "image": [reference],
        "negative_prompt": " ",
        "num_inference_steps": 40,
        "true_cfg_scale": 4.0,
        "guidance_scale": 1.0,
        "num_images_per_prompt": 1,
    }
    records = []
    _gallery_copy(reference_path, "qwen_edit_reference")
    for arm, prompt in (("raw", EDIT_RAW), ("pe", EDIT_PE)):
        output = pipe(
            prompt=prompt,
            generator=torch.Generator(device="cuda").manual_seed(SEED),
            **common,
        ).images[0]
        path = destination / f"{arm}.png"
        output.save(path)
        _gallery_copy(path, f"qwen_edit_{arm}")
        records.append(
            {
                "arm": arm,
                "prompt": prompt,
                "reference": str(reference_path.relative_to(ROOT)),
                "path": str(path.relative_to(ROOT)),
                "num_inference_steps": common["num_inference_steps"],
                "true_cfg_scale": common["true_cfg_scale"],
                "guidance_scale": common["guidance_scale"],
            }
        )
    _save_manifest("qwen_image_edit_2511", records)


def hunyuan() -> None:
    import torch
    from transformers.cache_utils import StaticLayer

    destination = OUTPUTS / "hunyuan_image_3"
    destination.mkdir(parents=True, exist_ok=True)
    # The local upstream checkout calls the pre-Transformers-5 one-argument
    # cache initializer. Keep this compatibility shim experiment-local.
    original_lazy_initialization = StaticLayer.lazy_initialization

    def compatible_lazy_initialization(
        layer: StaticLayer,
        key_states: torch.Tensor,
        value_states: torch.Tensor | None = None,
    ) -> None:
        original_lazy_initialization(
            layer,
            key_states,
            key_states if value_states is None else value_states,
        )

    StaticLayer.lazy_initialization = compatible_lazy_initialization
    sys.path.insert(0, str(HUNYUAN_SOURCE))
    from hunyuan_image_3 import HunyuanImage3ForCausalMM

    model = HunyuanImage3ForCausalMM.from_pretrained(
        HUNYUAN,
        attn_implementation="sdpa",
        trust_remote_code=True,
        torch_dtype="auto",
        device_map="auto",
        moe_impl=os.environ.get("HUNYUAN_MOE_IMPL", "eager"),
        moe_drop_tokens=True,
    )
    model.load_tokenizer(str(HUNYUAN))
    records = []
    for arm, prompt in (("raw", HUNYUAN_RAW), ("pe", HUNYUAN_PE)):
        torch.manual_seed(SEED)
        _, images = model.generate_image(
            prompt=prompt,
            seed=SEED,
            image_size="1024x1024",
            diff_infer_steps=30,
            verbose=2,
        )
        image = images[0]
        path = destination / f"{arm}.png"
        image.save(path)
        _gallery_copy(path, f"hunyuan_t2i_{arm}")
        records.append(
            {
                "arm": arm,
                "prompt": prompt,
                "path": str(path.relative_to(ROOT)),
                "image_size": "1024x1024",
                "diff_infer_steps": 30,
                "moe_impl": os.environ.get("HUNYUAN_MOE_IMPL", "eager"),
            }
        )
    _save_manifest("hunyuan_image_3", records)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("backend", choices=("qwen-t2i", "qwen-edit", "hunyuan", "all"))
    args = parser.parse_args()
    if args.backend in {"qwen-t2i", "all"}:
        qwen_t2i()
    if args.backend in {"qwen-edit", "all"}:
        qwen_edit()
    if args.backend in {"hunyuan", "all"}:
        hunyuan()


if __name__ == "__main__":
    main()
