# Scripts

Operational helpers for local Writers and optional generation runtimes. None of these are required
to view the gallery; `expand` only needs an OpenAI-compatible chat endpoint.

## Environment prefixes

| Prefix | Used by | Notes |
| --- | --- | --- |
| `OMNI_WRITER_*` | Python package (`Settings.from_env`), Qwen writer serve scripts | Canonical for expand/API |
| `OMNI_REWRITER_*` | Optional image/video **serve** scripts | Accepted as aliases; prefer matching `OMNI_WRITER_*` where listed below |
| `OMNI_H3_DEMO_VIDEOS` | Gallery / showcase thumb scripts | Local demo video tree only |
| `OMNI_AI_REVIEW_*` | Advisory PR review workflow helper | CI secret-backed |
| `REWRITER_*` / `HOST` / `PORT` | LingBot rewriter serve script | Script-local names |

Canonical Writer variables are documented in [`.env.example`](../.env.example).

### Preferred aliases for serve scripts

| Preferred (`OMNI_WRITER_*`) | Legacy (`OMNI_REWRITER_*`) | Scripts |
| --- | --- | --- |
| `OMNI_WRITER_IMAGE_MODEL` / `_HOST` / `_PORT` / `_GPUS` | `OMNI_REWRITER_IMAGE_*` | `serve_sglang_qwen_image.sh` |
| `OMNI_WRITER_HUNYUAN_MODEL` / `_HOST` / `_PORT` / `_TP` | `OMNI_REWRITER_HUNYUAN_*` | `serve_hunyuan_image3_vllm.sh` |
| `OMNI_WRITER_WAN_MODEL` + `OMNI_WRITER_VIDEO_HOST` / `_PORT` / `_GPUS` | `OMNI_REWRITER_WAN_MODEL`, `OMNI_REWRITER_VIDEO_*` | `serve_sglang_wan.sh`, `serve_vllm_omni_wan.sh` |

Scripts accept either name; if both are set, `OMNI_WRITER_*` wins.

## Inventory

| Script | Purpose |
| --- | --- |
| `serve_qwen35_dev.sh` / `serve_qwen35_prod.sh` | Local vLLM Writer |
| `serve_sglang_qwen_image.sh` | Optional Qwen-Image SGLang |
| `serve_hunyuan_image3_vllm.sh` | Optional HunyuanImage custom-vLLM |
| `serve_sglang_wan.sh` / `serve_vllm_omni_wan.sh` | Optional WAN video serve (unverified compatibility) |
| `serve_lingbot_rewriter.sh` / `run_lingbot_video.sh` | LingBot rewriter / video helpers |
| `make_gallery_thumbs.sh` / `make_h3_pe_showcase_thumbs.sh` | Low-res GIF thumbs (no `.mp4` commits) |
| `check_model_contribution.py` | PR contract checker |
| `ai_review_pr.py` | Optional advisory model review |
