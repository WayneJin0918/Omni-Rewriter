# Real A/B generation provenance

Generated on 2026-08-06 using 8 × NVIDIA H200 (143771 MiB each), driver
570.124.06. Full-resolution outputs stay under gitignored `outputs/`; the
low-resolution WebP files under `docs/assets/gallery/image/` are committed.

## Qwen-Image-2512 T2I

- Model: `/pfs/weiyang/WISE_re/CKPT/Qwen/Qwen-Image-2512`
- RAW and PE: seed `20260806`, 1024×576, 30 steps, `true_cfg_scale=4.0`
- Runtime: `/pfs/weiyang/Miniconda3/envs/qwenimage`; torch `2.11.0+cu128`,
  diffusers `0.38.0.dev0`, transformers `5.3.0`
- Assets: `qwen_t2i_raw.webp`, `qwen_t2i_pe.webp`

## Qwen-Image-Edit-2511

- Model: `/pfs/weiyang/WISE_re/CKPT/Qwen/Qwen-Image-Edit-2511`
- Reference generated with Qwen-Image-2512 at seed `20260807`, 768×768
- RAW and PE edit: same reference, seed `20260806`, 40 steps,
  `true_cfg_scale=4.0`, `guidance_scale=1.0`
- Runtime: `/pfs/weiyang/Miniconda3/envs/qwenimage`; torch `2.11.0+cu128`,
  diffusers `0.38.0.dev0`, transformers `5.3.0`
- Assets: `qwen_edit_reference.webp`, `qwen_edit_raw.webp`, `qwen_edit_pe.webp`

## HunyuanImage-3.0 T2I

- Model: `/pfs/weiyang/WISE_re/CKPT/tencent/HunyuanImage-3.0`
- Source: `/pfs/weiyang/WISE_re/HunyuanImage-3.0` at
  `d280425cf453a153e5846c725af58de39c10b09f`
- RAW and PE: seed `20260806`, 1024×1024, 30 diffusion steps
- Runtime: `/pfs/weiyang/Miniconda3/envs/hyimage`; torch `2.10.0+cu128`,
  transformers `5.14.1`
- Compatibility: the experiment applies a local `StaticLayer` initializer shim
  because the upstream source calls the pre-Transformers-5 signature
- Assets: `hunyuan_t2i_raw.webp`, `hunyuan_t2i_pe.webp`
