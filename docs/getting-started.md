# Getting started

[中文](getting-started_zh.md) · [Documentation index](index.md)

## Install

Omni-Rewriter requires Python 3.11+. The package expands and validates prompts; model servers and
generation checkpoints are separate runtime choices.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[cli,server]"
```

Configure an OpenAI-compatible writer backend through the environment. The project does not load
`.env` automatically. Gallery demos need no GPU; `expand` needs any chat endpoint that returns
structured JSON.

```bash
cp .env.example .env
# Hosted Writer (no local checkpoint):
# export OMNI_WRITER_BACKEND_BASE_URL=https://api.openai.com/v1
# export OMNI_WRITER_BACKEND_MODEL=gpt-5.6
# export OMNI_WRITER_BACKEND_API_KEY=sk-...
set -a; source .env; set +a
```

Copy-paste requests live in [`examples/requests/`](../examples/requests/). Optional Qwen/vLLM
scripts are development conveniences for open Writers, not image/video generation runtimes.

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

Seedance video PE (default render is fused natural text; set `seedance_render=json` for JSON):

```bash
omni-rewriter expand examples/requests/seedance_t2va_kitchen.json --output seedance
```

See [Seedance PE](seedance-pe.md). Default video dialect remains H3 when `video_pe_profile` is unset.

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
[Image PE](image-pe.md) for request and ratio constraints.

## Validate and evaluate

```bash
omni-rewriter validate output.json
omni-rewriter eval output.json
omni-rewriter eval tests/fixtures/manifest.jsonl --manifest
```

These commands verify schemas and dialect grammar. They do not generate media or measure
perceptual quality.

## Optional API

```bash
uvicorn 'omni_rewriter.api:create_app' --factory --host 127.0.0.1 --port 8080
curl -sS -X POST http://127.0.0.1:8080/v1/expand \
  -H 'content-type: application/json' --data @request.json
```

Also available: `GET /health`, `POST /v1/validate`, and OpenAPI docs at `/docs`.

## Generate only when requested

`expand` returns typed JSON and rendered text. To create media, explicitly connect a compatible
adapter or runner. The repository ships H3/MiniMax clients plus optional image/video adapters
(Qwen-Image HTTP, HunyuanImage custom-vLLM, Wan Omni mapping, LingBot runner); live compatibility
is evidence-scoped. See [Generation adapters](generation-adapters.md).

Bind the HTTP API to loopback unless you intentionally open it. Local filesystem media paths are
denied by default for `create_app` (set `OMNI_WRITER_ALLOW_LOCAL_MEDIA=1` only for trusted hosts).
