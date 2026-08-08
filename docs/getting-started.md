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
`.env` automatically:

```bash
cp .env.example .env
set -a; source .env; set +a
```

The included Qwen/vLLM scripts are development conveniences for the writer model, not generation
runtimes for image or video outputs.

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
adapter or runner. The repository currently implements H3/MiniMax clients; other model families
have different upstream runtimes and are not interchangeable. See
[Generation adapters](generation-adapters.md).
