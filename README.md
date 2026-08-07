# Omni-Rewriter

[中文说明](README_zh.md) · [Documentation](docs/index.md) · [Getting started](docs/getting-started.md) ·
[Contributing](CONTRIBUTING.md) · [Architecture](docs/architecture.md) ·
[H3 PE harness](docs/h3-pe-harness.md) · [Image PE](docs/image-pe.md) ·
[Generation adapters](docs/generation-adapters.md) · [Evaluation](docs/evaluation.md) ·
[Roadmap](ROADMAP.md)

<p align="center"><a href="docs/assets/gallery/index.html">Open the low-resolution RAW vs PE video gallery</a></p>

## A framework for prompt expansion

Omni-Rewriter is an open, model-extensible **prompt-expansion (PE) framework**. It turns casual
multimodal intent into **typed, validated, generator-oriented intermediate text**. H3 video,
Seedream-style image, and Qwen-Image-Edit-style image packing are the first dialects—not the
boundary of the framework.

The framework separates concerns:

1. a transport-neutral request captures intent, media, task, and metadata;
2. a PE profile analyzes and drafts a typed intermediate representation;
3. deterministic validators reject or repair malformed output within a fixed budget;
4. a renderer serializes the result for a target prompt dialect;
5. an optional adapter may submit that rendered prompt to a compatible generator.

**Expand is not generate.** `omni-rewriter expand` produces validated text/JSON; it does not load
generation weights, allocate a diffusion/video runtime, or create media. Generation occurs only
when an application explicitly invokes an adapter or independent runner.

We welcome contributions: dialects, validators, adapters, experiments, docs, and (later) SFT/RL
pipelines. See [CONTRIBUTING.md](CONTRIBUTING.md) and [ROADMAP.md](ROADMAP.md).

Omni-Rewriter provides:

- Typed request/output models and deterministic validation
- A bounded analyze → draft → repair agent
- Video PE for MiniMax-H3 (T2VA / I2VA / FL2VA / L2VA / Ref2VA)
- Image PE dialects aligned with Seedream-style and Qwen-Image-Edit-style packing
- Optional adapters for local/hosted generation (expand ≠ generate)

This project does **not** claim to reproduce, reverse engineer, or match MiniMax's official
Context-IR implementation, Seedream internals, or any private vendor behavior. Public examples and
documented request shapes inform compatibility profiles; they are not evidence of private
implementation parity.

## Model and runtime compatibility

“PE profile” means Omni-Rewriter can shape or validate text for that family. “Generation path”
describes an upstream runtime, not a bundled dependency or an end-to-end guarantee.

| Model family | PE status | Evidence-backed generation path | Omni-Rewriter integration |
| --- | --- | --- | --- |
| MiniMax H3 | Implemented video profile | Public MiniMax API or a compatible `/v1/videos` service | `MiniMaxClient` and `H3Client` implemented |
| Seedream-style image | Implemented image profile | Provider-specific API/runtime | PE implemented; provider adapter remains contribution scope |
| Qwen-Image / Qwen-Image-Edit | Implemented image/edit packing | Qwen-Image-2512 has native SGLang-Diffusion support ([SGLang v0.5.7](https://github.com/sgl-project/sglang/releases/tag/v0.5.7), [registry](https://github.com/sgl-project/sglang/blob/main/python/sglang/multimodal_gen/registry.py)) | `OpenAIImagesClient` implemented; local Qwen T2I/Edit recipes and real A/B included |
| HunyuanImage-3.0 | Seedream-style T2I PE can be rendered | Upstream documents a [model-specific vLLM fork](https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/vllm_infer/README.md) | `HunyuanImageVLLMClient` and local recipe implemented |
| Wan | H3-style video PE can be mapped | SGLang/vLLM-Omni implementations vary by release | `OmniVideosClient` + `WanOmniAdapter` implemented; live compatibility runtime-specific |
| LingBot Video | Typed structured caption | Upstream independent inference runner | `LingBotCaption`, bounded local runner, and optional two-stage rewriter implemented |
| vLLM-Omni routes | None assumed | Upstream lists several image/video families in its [support matrix](https://docs.vllm.ai/projects/vllm-omni/en/latest/models/supported_models/) | **Unverified here**; no end-to-end Omni-Rewriter compatibility claim |

Runtime support changes quickly. Pin upstream versions and validate payloads, hardware support, and
output quality in your own environment. See
[generation adapters](docs/generation-adapters.md) for evidence scope and integration boundaries.

## Features

- **Video PE:** T2VA, I2VA, FL2VA, L2VA, and Ref2VA routing with H3 grammar validation
  (tightened against public H3 skill contracts under `docs/references/`).
- **Image PE:** `t2i` / `i2i` / `image_edit` with Seedream-aligned and Qwen-Image-Edit-aligned
  dialects (`prompt` + `ratio`, tagged Seedream render).
- OpenAI-compatible multimodal writer backend, tested with local Qwen served by vLLM.
- Strict Pydantic output schemas, timeline/reference grammar checks, and bounded repair attempts.
- CLI and optional FastAPI entry points.
- H3/MiniMax, OpenAI-compatible image, Omni video/WAN, Hunyuan vLLM, and LingBot adapters.
- Deterministic single-case and JSONL-manifest evaluation.
- Bounded media loading with MIME checks, redirect limits, and public-address-only HTTP fetching.
- Experiments for raw-vs-PE comparison on video and image (plus low-res gallery clips above).

## Gallery (RAW vs PE)

<table>
  <tr><th>Scene</th><th>RAW</th><th>Omni-Rewriter PE</th></tr>
  <tr><td><code>s01_dialogue</code></td><td><img src="docs/assets/gallery/s01_dialogue_raw.gif" width="360" alt="s01 RAW"></td><td><img src="docs/assets/gallery/s01_dialogue_pe.gif" width="360" alt="s01 PE"></td></tr>
  <tr><td><code>s06_sneaker</code></td><td><img src="docs/assets/gallery/s06_sneaker_raw.gif" width="360" alt="s06 RAW"></td><td><img src="docs/assets/gallery/s06_sneaker_pe.gif" width="360" alt="s06 PE"></td></tr>
  <tr><td><code>s09_noir</code></td><td><img src="docs/assets/gallery/s09_noir_raw.gif" width="360" alt="s09 RAW"></td><td><img src="docs/assets/gallery/s09_noir_pe.gif" width="360" alt="s09 PE"></td></tr>
  <tr><td><code>s10_phone_call</code></td><td><img src="docs/assets/gallery/s10_phone_call_raw.gif" width="360" alt="s10 RAW"></td><td><img src="docs/assets/gallery/s10_phone_call_pe.gif" width="360" alt="s10 PE"></td></tr>
</table>

Regenerate with `scripts/make_gallery_thumbs.sh` after local experiment videos exist.

### Real image generation

<table>
  <tr><th>Model/task</th><th>RAW</th><th>Omni-Rewriter PE</th></tr>
  <tr><td>Qwen-Image-2512 T2I</td><td><img src="docs/assets/gallery/image/qwen_t2i_raw.webp" width="360" alt="Qwen T2I RAW"></td><td><img src="docs/assets/gallery/image/qwen_t2i_pe.webp" width="360" alt="Qwen T2I PE"></td></tr>
  <tr><td>Qwen-Image-Edit-2511</td><td><img src="docs/assets/gallery/image/qwen_edit_raw.webp" width="360" alt="Qwen Edit RAW"></td><td><img src="docs/assets/gallery/image/qwen_edit_pe.webp" width="360" alt="Qwen Edit PE"></td></tr>
  <tr><td>HunyuanImage-3.0 T2I</td><td><img src="docs/assets/gallery/image/hunyuan_t2i_raw.webp" width="360" alt="Hunyuan RAW"></td><td><img src="docs/assets/gallery/image/hunyuan_t2i_pe.webp" width="360" alt="Hunyuan PE"></td></tr>
</table>

[Open image gallery with prompts and reference image](docs/assets/gallery/image/index.html).

## Quickstart

Requirements: Python 3.11+, a compatible local checkpoint, and enough GPU memory for that
checkpoint. vLLM is a runtime prerequisite for the included model-serving scripts, not a Python
package dependency of Omni-Rewriter.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[cli,server]"
```

Start the local development writer model. The default checkpoint is a real local path used by
this deployment:

```bash
scripts/serve_qwen35_dev.sh
```

The dev script serves `/pfs/weiyang/WISE_re/CKPT/Qwen/Qwen3.5-9B` as
`Qwen/Qwen3.5-9B`. For the larger deployment:

```bash
scripts/serve_qwen35_prod.sh
```

Both scripts accept environment overrides and append additional vLLM arguments from `"$@"`:

```bash
OMNI_WRITER_MODEL=/models/Qwen3.5-9B \
OMNI_WRITER_SERVED_MODEL_NAME=my-qwen \
OMNI_WRITER_MAX_MODEL_LEN=16384 \
OMNI_WRITER_TENSOR_PARALLEL_SIZE=2 \
OMNI_WRITER_GPU_MEMORY_UTILIZATION=0.88 \
scripts/serve_qwen35_dev.sh --disable-log-requests
```

Configure Omni-Rewriter. It reads the process environment directly and intentionally does not load
`.env` files:

```bash
cp .env.example .env
set -a; source .env; set +a
```

Create `request.json`:

```json
{
  "prompt": "A handmade kite catches an evening breeze and turns above a grassy hill.",
  "duration_seconds": 6,
  "metadata": {
    "aspect_ratio": "16:9",
    "seed": "7"
  }
}
```

Run the CLI:

```bash
omni-rewriter expand request.json
omni-rewriter expand request.json --output h3
omni-rewriter validate output.json
```

Run the API:

```bash
uvicorn 'omni_rewriter.api:create_app' --factory --host 127.0.0.1 --port 8080
curl -sS http://127.0.0.1:8080/health
curl -sS -X POST http://127.0.0.1:8080/v1/expand \
  -H 'content-type: application/json' \
  --data @request.json
```

`POST /v1/validate` accepts either an output object or
`{"request": <RewriteRequest>, "output": <rewrite>}`. OpenAPI documentation is available at
`/docs` when the FastAPI server is running.

## Task format and routing

Every entry point accepts the same strict `RewriteRequest`:

```json
{
  "prompt": "Animate the supplied first frame.",
  "duration_seconds": 5,
  "media": [
    {
      "media_type": "image",
      "role": "first_frame",
      "uri": "./frame.png",
      "name": "frame.png",
      "mime_type": "image/png"
    }
  ],
  "task": "i2va",
  "metadata": {}
}
```

`prompt` is required; `duration_seconds` is positive; `media` supports image, video, and audio
references; metadata values are strings. The task may be omitted and is inferred as follows:

- no media → `t2va`
- one `first_frame` image → `i2va`
- one `last_frame` image → `l2va`
- one first-frame plus one last-frame image → `fl2va`
- every other non-empty media combination → `ref2va`

An explicitly supplied task must agree with the inferred route, except that `ref2va` may be
selected for any non-empty reference set. H3 adapters further require an integer duration from
4 through 15 seconds. See [the architecture guide](docs/architecture.md) for output schemas and
the validation lifecycle.

## Architecture

The runtime pipeline is:

1. validate and route a transport-neutral request;
2. load bounded media and create an OpenAI-compatible multimodal message;
3. ask the writer model for a structured analysis;
4. draft a typed base or Ref2VA rewrite;
5. deterministically validate schema, timeline, labels, and task/duration consistency;
6. retry a bounded repair loop when validation fails;
7. render H3-oriented text or pass a request to a generation adapter.

CLI and HTTP call the same service layer. Network clients are asynchronous and secrets use
Pydantic `SecretStr`. Details and component boundaries are in
[docs/architecture.md](docs/architecture.md).

## Generation adapters

The adapters are explicit clients, not part of the default `expand` pipeline:

- `H3Client` targets a local SGLang-style `/v1/videos` service and can submit, poll, and download.
- `MiniMaxClient` targets the public MiniMax H3 Context-IR, video-generation, and regeneration
  endpoints. It requires `MINIMAX_API_KEY`.

Endpoint mappings, payload differences, runtime evidence, and planned boundaries are documented in
[docs/generation-adapters.md](docs/generation-adapters.md). H3-specific examples remain in
[docs/h3-adapters.md](docs/h3-adapters.md). Public APIs can change; confirm current model
availability, versions, quotas, hardware support, and terms before production use.

## Evaluation

Evaluation is deterministic and does not call a model unless an application supplies an optional
judge:

```bash
omni-rewriter eval output.json
omni-rewriter eval examples/fixtures/manifest.jsonl --manifest
```

Metrics include schema pass, timeline pass, field completeness, shot/timestamp counts, and
reference-definition consistency. These checks measure format conformance, not perceptual video
quality, prompt faithfulness, safety, or human preference. See
[docs/evaluation.md](docs/evaluation.md).

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `OMNI_WRITER_BACKEND_BASE_URL` | `http://127.0.0.1:8000/v1` | OpenAI-compatible writer URL |
| `OMNI_WRITER_BACKEND_MODEL` | `Qwen/Qwen3.5-122B-A10B` | served writer model name |
| `OMNI_WRITER_BACKEND_API_KEY` | unset | optional writer bearer token |
| `OMNI_WRITER_TIMEOUT` | `120` | writer request timeout, seconds |
| `OMNI_WRITER_RETRIES` | `2` | retry count for transient writer failures |
| `OMNI_WRITER_TEMPERATURE` | `0.2` | writer sampling temperature |
| `OMNI_WRITER_MAX_TOKENS` | unset | optional completion limit |
| `OMNI_WRITER_ENABLE_THINKING` | `false` | Qwen chat-template thinking switch |
| `OMNI_WRITER_MAX_REPAIRS` | `2` | maximum validation repair calls |
| `OMNI_WRITER_H3_BASE_URL` | `http://127.0.0.1:30000` | local H3 service |
| `OMNI_WRITER_H3_API_KEY` | unset | optional local H3 bearer token |
| `OMNI_WRITER_H3_TIMEOUT` | `60` | local H3 request timeout |
| `OMNI_WRITER_H3_POLL_INTERVAL` | `2` | poll interval |
| `OMNI_WRITER_H3_POLL_TIMEOUT` | `900` | total poll deadline |
| `OMNI_WRITER_H3_MAX_DOWNLOAD_BYTES` | `2147483648` | video download cap |
| `MINIMAX_API_KEY` | unset | MiniMax bearer token |
| `MINIMAX_API_BASE` | `https://api.minimax.io` | MiniMax API origin |
| `MINIMAX_TIMEOUT` | `60` | MiniMax request timeout |
| `MINIMAX_POLL_INTERVAL` | `2` | MiniMax poll interval |
| `MINIMAX_POLL_TIMEOUT` | `900` | MiniMax poll deadline |

Legacy aliases `OMNI_WRITER_BASE_URL`, `OMNI_WRITER_MODEL`, `OMNI_WRITER_API_KEY`, and
`MINIMAX_BASE_URL` are accepted. Script-only vLLM variables are documented in
[docs/architecture.md](docs/architecture.md).

## Security and SSRF

Treat every prompt, media URI, generated text, and remote response as untrusted.

- HTTP(S) media loading resolves every initial and redirected hostname and rejects non-global IP
  addresses by default. Redirects, duration, MIME types, and bytes are bounded.
- Local paths are supported. Therefore, exposing the API to untrusted callers can disclose files
  readable by the service account. Put the service behind authentication and authorize or disable
  local-path inputs at the application boundary.
- DNS checks reduce SSRF risk but are not a complete sandbox. Use egress filtering, a dedicated
  low-privilege account/container, an allowlist proxy, and network isolation in hostile
  environments.
- The local H3 downloader accepts a URL returned by the configured H3 service. Only connect it to
  a trusted service; enforce egress policy because that response URL is not separately SSRF
  filtered.
- Never commit `.env`, API keys, traces, prompts containing sensitive data, or generated media.
  Bind development services to loopback. Add authentication and TLS before remote exposure.

## Limitations

- This is an independent compatibility-oriented implementation, not official MiniMax software.
- H3-oriented formatting is validated locally but does not guarantee identical behavior or output
  quality from any generator.
- The writer depends on the selected model's structured-output and multimodal support.
- Default media preparation is limited to 20 MiB per item and a fixed MIME allowlist.
- The service has no built-in user authentication, authorization, rate limiting, moderation,
  persistence, queue, or distributed worker.
- H3/MiniMax adapters are library APIs and are not exposed as CLI generation commands.
- Evaluation checks structure, not rendered-video quality.

## Development

```bash
python -m pip install -e ".[dev]"
ruff check .
mypy src
pytest
python -m build
```

The CI workflow runs the same checks. No model checkpoint, MiniMax-H3 documentation, MiniMax-H3
weights, Qwen weights, or generated media is distributed in this repository.

## License and notices

Source code in this repository is licensed under Apache License 2.0. See [LICENSE](LICENSE) and
[NOTICE](NOTICE). Third-party model weights, documentation, services, and names remain subject to
their own licenses and terms.
