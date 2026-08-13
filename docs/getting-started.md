# Getting started

[中文](getting-started_zh.md) · [Documentation index](index.md)

## Install

Omni-Rewriter requires Python 3.11+. **Validate needs no GPU and no Writer.** Expand needs an
OpenAI-compatible chat endpoint. Generation checkpoints are a separate runtime choice.

```bash
python -m pip install omni-rewriter
curl -fsSL -o kite.json \
  https://raw.githubusercontent.com/WayneJin0918/Omni-Rewriter/v0.1.0/tests/fixtures/t2va_kite.json
omni-rewriter validate kite.json
```

Same checker in CI: `uses: WayneJin0918/Omni-Rewriter@v0.1.0` (see
[`pe-validate-action.md`](pe-validate-action.md)). Expand still needs a Writer.

From a git clone (CLI + optional HTTP server):

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[cli,server]"
```

Configure backends through the environment (the project does not load `.env` automatically).
Gallery demos need no GPU. Preferred path: **local SGLang Qwen3.6-35B-A3B Writer + local SGLang MiniMax-H3**;
hosted API Writers are a fallback. Expand ≠ generate.

```bash
cp .env.example .env
set -a; source .env; set +a
```

### Recommended: SGLang Qwen3.6-35B-A3B (Writer) + SGLang H3 (~30B FL2VA)

```bash
# Terminal A — language + vision Qwen chat Writer
# https://huggingface.co/Qwen/Qwen3.6-35B-A3B
export OMNI_WRITER_MODEL=Qwen/Qwen3.6-35B-A3B
export OMNI_WRITER_SERVED_MODEL_NAME=Qwen/Qwen3.6-35B-A3B
bash scripts/serve/serve_sglang_qwen_writer.sh

# Terminal B — MiniMax-H3 FL2VA (optional generate)
export OMNI_WRITER_H3_MODEL=/path/to/MiniMax-H3/FL2VA
export OMNI_WRITER_H3_NUM_GPUS=8
bash scripts/serve/serve_sglang_h3.sh

# Shell for expand
export OMNI_WRITER_BACKEND_BASE_URL=http://127.0.0.1:8000/v1
export OMNI_WRITER_BACKEND_MODEL=Qwen/Qwen3.6-35B-A3B
export OMNI_WRITER_H3_BASE_URL=http://127.0.0.1:30010
```

Serve helpers: [`scripts/serve/serve_sglang_qwen_writer.sh`](../scripts/serve/serve_sglang_qwen_writer.sh),
[`scripts/serve/serve_sglang_h3.sh`](../scripts/serve/serve_sglang_h3.sh). H3 client notes:
[H3 adapters](dialects/h3-adapters.md).

### Fallback: hosted API Writer

```bash
export OMNI_WRITER_BACKEND_BASE_URL=https://api.openai.com/v1
export OMNI_WRITER_BACKEND_MODEL=gpt-5.6
export OMNI_WRITER_BACKEND_API_KEY=sk-...
```

Copy-paste requests: [`examples/requests/`](../examples/requests/). vLLM Qwen3.5 scripts remain
available as an alternate Writer serve path (`serve_qwen35_*.sh`).

## Expand a video intent

Video tasks require `duration_seconds`:

```json
{
  "prompt": "A handmade kite catches an evening breeze above a grassy hill.",
  "duration_seconds": 6,
  "metadata": {"aspect_ratio": "16:9"}
}
```

```bash
omni-rewriter expand request.json
omni-rewriter expand request.json --output h3
```

With no media, routing infers `t2va`. First-frame, last-frame, endpoint-pair, and arbitrary
reference inputs route to `i2va`, `l2va`, `fl2va`, and `ref2va` respectively.

Seedance video PE (default render is the public Seedance 2.5 natural template; use
`seedance_render=fused` for legacy labeled text, or `seedance_render=json` for JSON):

```bash
omni-rewriter expand examples/requests/seedance_t2va_kitchen.json --output seedance
```

See [Seedance PE](dialects/seedance-pe.md). Default video dialect remains H3 when `video_pe_profile` is unset.

## Expand an image intent

Image tasks must omit `duration_seconds`:

```json
{
  "prompt": "Create a rain-soaked neon storefront poster; preserve the title exactly.",
  "task": "t2i",
  "metadata": {"image_pe_profile": "seedream"}
}
```

Use `seedream` for a visual-blueprint render or `qwen_image_edit` for imperative editing. See
[Image PE](dialects/image-pe.md) for request and ratio constraints.

## Validate and evaluate

```bash
omni-rewriter validate output.json
omni-rewriter eval output.json
omni-rewriter eval tests/fixtures/manifest.jsonl --manifest
```

These commands verify schemas and dialect grammar. They do not generate media or measure
perceptual quality.

## Reconstruct a local clip (v2pe)

Read a short local mp4 into validated H3 `t2va` PE. The source file stays on disk; `expand` never
sees the original bytes. Expand ≠ generate.

```bash
# No Writer: ffmpeg evidence pack only
omni-rewriter reconstruct clip.mp4 --pack-only --pack-dir /tmp/pe-pack

# No GPU: validate the synthetic observation envelope
omni-rewriter validate docs/design/examples/observation_kite.json

# Text Writer: observation JSON → same draft/validate/repair loop
omni-rewriter reconstruct --from-observation docs/design/examples/observation_kite.json

# Vision Writer: JPEG keyframes → VideoObservation → H3 PE
omni-rewriter reconstruct clip.mp4 --pack-dir /tmp/pe-pack
```

HTTP `POST /v1/reconstruct` accepts `VideoObservation` JSON only (no mp4 upload). Local smoke:

```bash
PYTHONPATH=src python scripts/smoke_reconstruct.py
PYTHONPATH=src python scripts/smoke_reconstruct.py --clip /path/to/short.mp4
```

Clips longer than 45s are rejected for observe. H3 **generate** stays on the public 4–15s
window; longer sources replay the first 15s. Design:
[Video reconstruct PE](design/video-reconstruct-pe.md).

## Optional API

```bash
uvicorn 'omni_rewriter.api:create_app' --factory --host 127.0.0.1 --port 8080
curl -sS -X POST http://127.0.0.1:8080/v1/expand \
  -H 'content-type: application/json' --data @request.json
```

Also available: `GET /health`, `POST /v1/validate`, `POST /v1/reconstruct` (observation JSON
only), and OpenAPI docs at `/docs`.

## Generate only when requested

`expand` returns typed JSON and rendered text. To create media, explicitly connect a compatible
adapter or runner. The repository ships H3/MiniMax clients plus optional image/video adapters
(Qwen-Image HTTP, HunyuanImage custom-vLLM, Wan Omni mapping, LingBot runner); live compatibility
is evidence-scoped. See [Generation adapters](dialects/generation-adapters.md).

Bind the HTTP API to loopback unless you intentionally open it. Local filesystem media paths are
denied by default for `create_app` (set `OMNI_WRITER_ALLOW_LOCAL_MEDIA=1` only for trusted hosts).
