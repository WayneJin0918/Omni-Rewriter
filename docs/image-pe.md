# Image PE (Seedream / Qwen-Image-Edit)

[中文](image-pe_zh.md) · [Framework architecture](architecture.md)

Image PE is a profile family in the general Omni-Rewriter framework. It uses the same lifecycle as
H3 video:
analyze → draft → deterministic validate → bounded repair.

The profile outputs prompt text and metadata; it does not run Seedream, Qwen-Image, SGLang, or any
other image generator. Public prompt shapes do not establish parity with private model internals.

## Tasks

| Task | When | Duration |
|---|---|---|
| `t2i` | Text-to-image (optional refs) | omit `duration_seconds` |
| `i2i` | Image-to-image with references | omit; requires media |
| `image_edit` | Edit-oriented dialect (defaults to Qwen-Image-Edit rules) | omit; requires media |

Video tasks still require `duration_seconds`. Image tasks reject it.

## Profiles

Set `metadata.image_pe_profile`:

- `seedream` (default for `t2i` / `i2i`) — emotion-free visual blueprint + tagged render
- `qwen_image_edit` (default for `image_edit`) — imperative edit instruction; `render()` is the prompt body

## Output schema

```json
{
  "task": "t2i",
  "profile": "seedream",
  "prompt": "Single-paragraph visual description…",
  "ratio": "16:9"
}
```

`ratio` must be one of `21:9`, `16:9`, `3:2`, `4:3`, `1:1`, `3:4`, `2:3`, `9:16`, or `[image N]`.

Seedream-packaged render:

```text
<prompt>
…
</prompt>
<ratio>
16:9
</ratio>
```

## Example request

```json
{
  "prompt": "做一张横版海报，主标题写“夏日限定”，霓虹寿司店门口，雨夜反光地面",
  "task": "t2i",
  "metadata": {
    "image_pe_profile": "seedream"
  }
}
```

```bash
omni-rewriter expand request.json
omni-rewriter expand request.json --output image
```

## Experiment

See `experiments/image-pe-raw-vs-pe/` for raw-vs-PE text comparison (Seedream + Qwen-Image-Edit cases) and the intranet compare page.
