# LTX-2.5 video PE

[中文](ltx-pe_zh.md) · [Framework architecture](../architecture.md)

LTX-2.5 is a **video PE profile** in Omni-Rewriter: schema → validate → paragraph render. It does
**not** download Lightricks weights or run `ltx_pipelines` during `expand`. Expand ≠ generate.

This profile follows the **public LTX-2 prompting guide**: one flowing chronological paragraph,
literal cinematographer language, start with the action, keep within 200 words. It does **not**
reproduce private LTX training captions or unpublished prompt enhancers.

## Public evidence

- [Lightricks/LTX-2](https://github.com/Lightricks/LTX-2) README, “Prompting for LTX-2”: single
  flowing paragraph; action, movement, appearance, environment, camera, lighting, sudden events;
  ~200 words; [How to prompt for LTX-2](https://ltx.video/blog/how-to-prompt-for-ltx-2).
- Official distilled CLI: `python -m ltx_pipelines.distilled` with split LTX-2.5 components,
  `--prompt`, `--num-frames` (`8 * k + 1`), `--height`/`--width` divisible by 32, optional
  `--image PATH FRAME_IDX STRENGTH`.
- Weights: [Lightricks/LTX-2.5](https://huggingface.co/Lightricks/LTX-2.5). Paper:
  [arXiv:2601.03233](https://arxiv.org/abs/2601.03233).

PE status: **implemented**. Adapter status: optional official-CLI runner
(`LTXVideoRunner` / `scripts/run_ltx25.sh`). Live runtime: **unverified** in this repository
until a local generate is recorded. Set `OMNI_LTX_CHECKPOINT` to your split root (official
layout `models/ltx-2.5`); do not commit machine paths.

## Routing

Set `metadata.video_pe_profile=ltx` (default video profile remains `h3`).

| Task | Media | Generate-time mapping |
| --- | --- | --- |
| `t2va` | none | Text-to-A/V |
| `i2va` | 1 image | `--image PATH 0 STRENGTH` |
| `l2va` | 1 image | `--image PATH last STRENGTH` |
| `fl2va` | 2 images | first frame 0 + last frame `num_frames-1` |
| `ref2va` | ≥1 image | one `--image` flag per still |

`duration_seconds` is required on the request/schema. Image tasks must omit it. Do **not** put
aspect ratio, duration, or resolution into the rendered paragraph. Official generate defaults
used by the runner are 24 fps and `num_frames = 8 * k + 1` (5 s → 121 frames).

## Output schema (`LTXRewrite`)

```json
{
  "task": "t2va",
  "profile": "ltx",
  "duration_seconds": "5",
  "action": "…",
  "movements": "…",
  "appearance": "…",
  "environment": "…",
  "camera": "…",
  "lighting": "…",
  "audio": "…",
  "changes": null,
  "generate_audio": true
}
```

Default render is one paragraph (`ltx_render=paragraph`). Use `ltx_render=json` for the schema.

```bash
omni-rewriter expand examples/requests/ltx_t2va_workshop.json --output ltx
omni-rewriter expand examples/requests/ltx_i2va_portrait.json --output ltx
```

## Fixtures

- `tests/fixtures/ltx/t2va_workshop.json`
- `tests/fixtures/ltx/i2va_portrait.json`
- Example requests under `examples/requests/ltx_*.json`
