# Generation adapters and runtime compatibility

[中文](generation-adapters_zh.md) · [Documentation index](index.md)

## Boundary: expand is not generate

Omni-Rewriter's core contract ends at typed rewrite JSON and rendered PE text. It does not infer
that a model runtime is installed, translate every profile into every provider payload, or submit a
generation task during `expand`.

Adapters are explicit boundary clients. They must define payload mapping, authentication, polling,
timeouts, idempotency expectations, download limits, and version assumptions. A prompt profile and
a generation runtime are compatible only after an integration test proves that exact path.

## Compatibility matrix

| Model family | Prompt-expansion support | Documented generation runtime/API | Repository status |
| --- | --- | --- | --- |
| MiniMax H3 | Implemented: Base and Ref video profiles | MiniMax public API; compatible local `/v1/videos` services | `MiniMaxClient` and `H3Client` implemented; see [H3 adapters](h3-adapters.md) |
| Seedream image | Implemented: `seedream` packing | Provider-specific service | Provider-specific generation adapter not bundled |
| Qwen-Image / Qwen-Image-Edit | Implemented: image and edit packing | Qwen-Image-2512 is registered natively in SGLang-Diffusion | `OpenAIImagesClient`; local Diffusers A/B recipe |
| HunyuanImage-3.0 | Seedream T2I packing can be used | Upstream model-specific vLLM fork | `HunyuanImageVLLMClient`; local upstream runner recipe |
| Wan | H3-style video output can be mapped | SGLang/vLLM-Omni contracts vary by release | `OmniVideosClient` + `WanOmniAdapter` |
| LingBot Video | `LingBotCaption` schema | Independent upstream runner | Bounded subprocess runner + optional two-stage rewriter |
| vLLM-Omni paths | No compatibility inferred | Upstream publishes a broad image/video support matrix | **Unverified by this repository** |

## Evidence and qualifications

### Qwen-Image-2512: native SGLang-Diffusion support

SGLang's [v0.5.7 release](https://github.com/sgl-project/sglang/releases/tag/v0.5.7) announces
day-zero Qwen-Image-2512 support, and its
[multimodal registry](https://github.com/sgl-project/sglang/blob/main/python/sglang/multimodal_gen/registry.py)
registers `Qwen/Qwen-Image-2512`. `OpenAIImagesClient` maps validated prompts to
`/v1/images/generations`, accepts bounded base64 or URL results, and is covered by mock transport
tests. The repository does not certify every SGLang version, hardware backend, quantization, or
LoRA combination.

### HunyuanImage-3.0: custom vLLM fork

Tencent's [vLLM inference guide](https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/vllm_infer/README.md)
instructs users to install a `feature/hunyuan_image_3.0` fork/branch and launch its model-specific
server. Treat that as a separate runtime, not evidence that stock vLLM used for Omni-Rewriter's
writer backend can generate Hunyuan images.

`HunyuanImageVLLMClient` implements only that documented extension:
`/v1/chat/completions`, `task_type=hunyuan_image3`, `task_extra_kwargs`, and a bounded top-level
base64 `image`. It is intentionally not presented as stock OpenAI compatibility.

### Wan: Omni-style video APIs

Alibaba Model Studio documents asynchronous
[Wan text-to-video](https://www.alibabacloud.com/help/en/model-studio/text-to-video-api-reference)
and [reference-to-video](https://help.aliyun.com/en/model-studio/wan-video-to-video-api-reference)
APIs. `OmniVideosClient` supports a configurable JSON/multipart submit → poll → content contract;
`WanOmniAdapter` maps model, duration, size, seed, and reference media. Runtime endpoint details
still need to be validated against the pinned SGLang/vLLM-Omni release.

### LingBot-World: independent runner

LingBot-World's upstream repository provides its own
[`generate.py` / `torchrun` inference path](https://github.com/Robbyant/lingbot-world#inference).
Omni-Rewriter therefore uses an explicit bounded subprocess runner and does not claim LingBot
implements `/v1/videos`. The optional rewriter client keeps base expansion and LoRA JSON mapping
as two distinct OpenAI-compatible stages.

### vLLM-Omni: upstream-listed, locally unverified

The vLLM-Omni [supported-model table](https://docs.vllm.ai/projects/vllm-omni/en/latest/models/supported_models/)
currently lists Qwen-Image, HunyuanImage, and Wan variants. That fast-moving upstream table is not
an Omni-Rewriter integration test. Claims about end-to-end prompt shape, endpoint behavior,
version compatibility, and generated quality are therefore **unverified in this repository** until
reproducible adapter tests are added.

## Local reference recipes

The scripts are operational recipes, not core dependencies:

- `scripts/serve_sglang_qwen_image.sh`: Qwen-Image-2512 at
  `/pfs/weiyang/WISE_re/CKPT/Qwen/Qwen-Image-2512`.
- `scripts/serve_hunyuan_image3_vllm.sh`: HunyuanImage-3.0 through Tencent's vLLM fork.
- `scripts/serve_sglang_wan.sh` and `scripts/serve_vllm_omni_wan.sh`: WAN reference launchers;
  verify runtime/version support before use.
- `scripts/serve_lingbot_rewriter.sh`: base Qwen3.6-27B expansion plus
  `/pfs/weiyang/lingbot-video-rewriter-lora` JSON mapping.
- `scripts/run_lingbot_video.sh`: independent generation through
  `/pfs/weiyang/lingbot-video` and `/pfs/weiyang/lingbot-video-moe-30b-a3b`.

The LingBot stages are intentionally separate from the default Omni-Rewriter agent and from
`service.expand`.

## Adapter contribution requirements

New adapters should:

1. remain opt-in and separate from `service.expand`;
2. map a documented PE profile to a pinned public API/runtime contract;
3. reject unsupported tasks and metadata instead of silently dropping fields;
4. bound polling, downloads, retries, and remote redirects;
5. avoid blind retries of paid/non-idempotent submissions;
6. include mocked contract tests and a clearly labeled optional live test;
7. document data disclosure, secrets, licenses, quotas, and upstream version evidence;
8. avoid claims about private internals or quality parity.
