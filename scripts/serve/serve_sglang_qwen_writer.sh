#!/usr/bin/env bash
# Serve the recommended Qwen Writer over OpenAI-compatible chat (SGLang).
# Default: Qwen/Qwen3.6-35B-A3B — multimodal language + vision (expand + reconstruct observe).
# This is not an image/video generator. Expand ≠ generate.
# Public recipe: https://huggingface.co/Qwen/Qwen3.6-35B-A3B
# Official full-context SGLang launch uses --tp-size 8 --context-length 262144.
# PE defaults use a shorter context so a 4-GPU start is enough for most nodes.
set -euo pipefail

MODEL="${OMNI_WRITER_MODEL:-Qwen/Qwen3.6-35B-A3B}"
SERVED_MODEL_NAME="${OMNI_WRITER_SERVED_MODEL_NAME:-Qwen/Qwen3.6-35B-A3B}"
HOST="${OMNI_WRITER_SGLANG_HOST:-${OMNI_WRITER_VLLM_HOST:-127.0.0.1}}"
PORT="${OMNI_WRITER_SGLANG_PORT:-${OMNI_WRITER_VLLM_PORT:-8000}}"
TP="${OMNI_WRITER_TENSOR_PARALLEL_SIZE:-4}"
MEM="${OMNI_WRITER_SGLANG_MEM_FRACTION:-0.80}"
CONTEXT="${OMNI_WRITER_MAX_MODEL_LEN:-32768}"
REASONING_PARSER="${OMNI_WRITER_REASONING_PARSER:-qwen3}"

args=(
  --model-path "${MODEL}"
  --served-model-name "${SERVED_MODEL_NAME}"
  --host "${HOST}"
  --port "${PORT}"
  --tp-size "${TP}"
  --mem-fraction-static "${MEM}"
  --context-length "${CONTEXT}"
  --trust-remote-code
)
if [[ -n "${REASONING_PARSER}" ]]; then
  args+=(--reasoning-parser "${REASONING_PARSER}")
fi
args+=("$@")

if command -v sglang >/dev/null 2>&1; then
  exec sglang serve "${args[@]}"
fi

exec python -m sglang.launch_server "${args[@]}"
