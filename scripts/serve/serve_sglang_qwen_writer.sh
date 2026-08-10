#!/usr/bin/env bash
# Serve a small local Qwen Writer over OpenAI-compatible chat (SGLang).
# Used by Omni-Rewriter expand — not an image/video generator.
set -euo pipefail

MODEL="${OMNI_WRITER_MODEL:?Set OMNI_WRITER_MODEL to your local Qwen checkpoint (e.g. Qwen3.5-9B)}"
SERVED_MODEL_NAME="${OMNI_WRITER_SERVED_MODEL_NAME:-Qwen/Qwen3.5-9B}"
HOST="${OMNI_WRITER_SGLANG_HOST:-${OMNI_WRITER_VLLM_HOST:-127.0.0.1}}"
PORT="${OMNI_WRITER_SGLANG_PORT:-${OMNI_WRITER_VLLM_PORT:-8000}}"
TP="${OMNI_WRITER_TENSOR_PARALLEL_SIZE:-1}"
MEM="${OMNI_WRITER_SGLANG_MEM_FRACTION:-0.85}"
CONTEXT="${OMNI_WRITER_MAX_MODEL_LEN:-16384}"

if command -v sglang >/dev/null 2>&1; then
  exec sglang serve \
    --model-path "${MODEL}" \
    --served-model-name "${SERVED_MODEL_NAME}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --tp-size "${TP}" \
    --mem-fraction-static "${MEM}" \
    --context-length "${CONTEXT}" \
    --trust-remote-code \
    "$@"
fi

exec python -m sglang.launch_server \
  --model-path "${MODEL}" \
  --served-model-name "${SERVED_MODEL_NAME}" \
  --host "${HOST}" \
  --port "${PORT}" \
  --tp-size "${TP}" \
  --mem-fraction-static "${MEM}" \
  --context-length "${CONTEXT}" \
  --trust-remote-code \
  "$@"
