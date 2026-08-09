# Real image RAW vs PE samples

These low-resolution WebP files are derived from reproducible local runs. Labels
and prompts live in HTML/Markdown, not inside image pixels.

| Prefix | Model | Comparison |
|---|---|---|
| `qwen_t2i_*` | Qwen-Image-2512 | identical seed/size/steps, RAW vs PE prompt |
| `hunyuan_t2i_*` | HunyuanImage-3.0 | identical seed/ratio, RAW vs PE prompt |

Full-resolution generation remains local and gitignored. Use your own OpenAI-compatible
or custom-vLLM image endpoints via the adapters documented in
[`docs/dialects/generation-adapters.md`](../../dialects/generation-adapters.md).
